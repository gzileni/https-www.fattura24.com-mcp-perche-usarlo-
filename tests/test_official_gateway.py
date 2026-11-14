"""Offline OAuth + unified MCP tests against a synthetic official provider.

No Fattura24 account/API key/network; no real document or customer writes.
"""
import asyncio
import base64
import hashlib
import json
import os
import time
from urllib.parse import parse_qs, urlsplit

import httpx
from mcp.types import Tool, ToolAnnotations
from official_gateway import OfficialConnection, PrivateOAuthStorage, ConnectionRoutes
import server

TOOL = {"name": "report_bilancino", "description": "Demo ufficiale simulato", "inputSchema": {
    "type": "object", "properties": {"anno": {"type": "integer"}}, "required": ["anno"]},
    "annotations": {"readOnlyHint": True, "destructiveHint": False}}
RESULT = {"content": [{"type": "text", "text": "BILANCINO DIMOSTRATIVO"}],
          "structuredContent": {"demo": True, "ricavi": 1000, "costi": 600, "ebitda": 400}, "isError": False}


class DemoOfficial:
    def __init__(self):
        self.messages = []
        self.code_challenge = None
        self.verifier_checked = False
        self.refreshed = False
        self.token = "demo-official-token"
        self.result = RESULT

    def __call__(self, req):
        assert req.url.host == "www.app.fattura24.com"
        path = req.url.path
        if path.startswith('/.well-known/oauth-protected-resource'):
            return httpx.Response(200, json={"resource": "https://www.app.fattura24.com/mcp",
                "authorization_servers": ["https://www.app.fattura24.com"], "scopes_supported": ["mcp"]})
        if path.startswith('/.well-known/oauth-authorization-server'):
            return httpx.Response(200, json={"issuer": "https://www.app.fattura24.com",
                "authorization_endpoint": "https://www.app.fattura24.com/oauth/authorize",
                "token_endpoint": "https://www.app.fattura24.com/oauth/token",
                "registration_endpoint": "https://www.app.fattura24.com/oauth/register",
                "response_types_supported": ["code"], "grant_types_supported": ["authorization_code", "refresh_token"],
                "code_challenge_methods_supported": ["S256"], "token_endpoint_auth_methods_supported": ["none"]})
        if path == '/oauth/register':
            metadata = json.loads(req.content)
            assert metadata['redirect_uris'] == ['http://127.0.0.1:8765/oauth/callback']
            return httpx.Response(201, json={**metadata, "client_id": "demo-client"})
        if path == '/oauth/token':
            fields = parse_qs(req.content.decode())
            if fields['grant_type'] == ['refresh_token']:
                assert fields['refresh_token'] == ['demo-refresh-token']
                self.refreshed = True
                self.token = 'demo-refreshed-token'
                return httpx.Response(200, json={'access_token': self.token, 'refresh_token': 'demo-refresh-token', 'token_type': 'Bearer', 'expires_in': 3600, 'scope': 'mcp'})
            assert fields['code'] == ['demo-code']
            actual = base64.urlsafe_b64encode(hashlib.sha256(fields['code_verifier'][0].encode()).digest()).decode().rstrip('=')
            assert actual == self.code_challenge
            self.verifier_checked = True
            return httpx.Response(200, json={"access_token": "demo-official-token", "token_type": "Bearer", "expires_in": 3600, "scope": "mcp", "refresh_token": "demo-refresh-token"})
        assert path == '/mcp'
        if req.headers.get('authorization') != 'Bearer ' + self.token:
            # A local bridge credential must never reach the upstream.
            assert 'demo-local-token' not in req.headers.get('authorization', '')
            return httpx.Response(401, headers={'WWW-Authenticate': 'Bearer resource_metadata="https://www.app.fattura24.com/.well-known/oauth-protected-resource"'})
        if req.method != 'POST':
            return httpx.Response(405)
        msg = json.loads(req.content)
        self.messages.append(msg)
        method = msg['method']
        if method == 'notifications/initialized':
            return httpx.Response(202)
        if method == 'initialize':
            result = {'protocolVersion': '2025-03-26', 'capabilities': {'tools': {}}, 'serverInfo': {'name': 'DEMO-OFFICIAL', 'version': '1'}}
        elif method == 'tools/list':
            result = {'tools': [TOOL, {**TOOL, 'name': 'segnala_limite_connettore', 'annotations': {'readOnlyHint': False, 'destructiveHint': True}}]}
        elif method == 'tools/call':
            assert msg['params']['name'] == 'report_bilancino'
            assert msg['params']['arguments'] == {'anno': 2026}
            result = self.result
        else:
            return httpx.Response(400)
        return httpx.Response(200, json={'jsonrpc': '2.0', 'id': msg['id'], 'result': result})


def test_oauth_and_wrapper_share_one_mcp_endpoint(tmp_path, monkeypatch):
    async def run():
        monkeypatch.setenv('BRIDGE_TOKEN', 'demo-local-token')
        monkeypatch.setenv('BRIDGE_PUBLIC_URL', 'http://127.0.0.1:8765')
        monkeypatch.delenv('FATTURA24_API_KEY', raising=False)
        monkeypatch.setenv('FATTURA24_ENABLE_WRITES', 'false')
        fake = DemoOfficial()
        storage = PrivateOAuthStorage(tmp_path / 'oauth.json')
        connection = OfficialConnection(storage, httpx.MockTransport(fake))
        monkeypatch.setattr(server, 'official', connection)
        app = ConnectionRoutes(server.BearerGuard(server.backend), connection)
        async with server.mcp.session_manager.run():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url='http://127.0.0.1:8765') as client:
                assert (await client.post('/official/connect')).status_code == 401
                auth = {'Authorization': 'Bearer demo-local-token'}
                assert (await client.get('/oauth/callback?code=evil&state=evil')).status_code == 400
                headers = {**auth, 'Accept': 'application/json, text/event-stream', 'MCP-Protocol-Version': '2025-03-26'}
                async def rpc(method, params=None):
                    payload = {'jsonrpc': '2.0', 'id': 1, 'method': method}
                    if params is not None:
                        payload['params'] = params
                    r = await client.post('/mcp', headers=headers, json=payload)
                    assert r.status_code == 200, r.text
                    if r.headers.get("Mcp-Session-Id"):
                        headers["Mcp-Session-Id"] = r.headers["Mcp-Session-Id"]
                    return r.json()['result']
                await rpc('initialize', {'protocolVersion': '2025-03-26', 'capabilities': {}, 'clientInfo': {'name': 'demo', 'version': '1'}})
                before = await rpc('tools/list', {})
                assert 'connect_fattura24' in {t['name'] for t in before['tools']}
                assert 'report_bilancino' not in {t['name'] for t in before['tools']}
                connected = await rpc('tools/call', {'name': 'connect_fattura24', 'arguments': {}})
                flow = connected['structuredContent']
                repeat = await rpc('tools/call', {'name': 'connect_fattura24', 'arguments': {}})
                assert repeat['structuredContent']['authorization_url'] == flow['authorization_url']
                # A client declaring URL elicitation receives the native MCP URL request.
                headers.pop('Mcp-Session-Id', None)
                await rpc('initialize', {'protocolVersion': '2025-11-25', 'capabilities': {'elicitation': {'url': {}}}, 'clientInfo': {'name': 'demo-native', 'version': '1'}})
                native = await client.post('/mcp', headers=headers, json={'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'connect_fattura24','arguments':{}}})
                assert native.json()['error']['code'] == -32042
                assert native.json()['error']['data']['elicitations'][0]['url'] == flow['authorization_url']
                assert flow['state'] == 'awaiting_authorization', flow
                query = parse_qs(urlsplit(flow['authorization_url']).query)
                fake.code_challenge = query['code_challenge'][0]
                assert query['code_challenge_method'] == ['S256']
                assert not connection.accept_callback('demo-code', 'wrong-state')
                assert (await client.get('/oauth/callback', params={'code': 'demo-code', 'state': query['state'][0]})).status_code == 200
                await asyncio.wait_for(connection.login_task, 10)
                assert connection.state == 'ready'
                assert fake.verifier_checked
                ready = await rpc('tools/call', {'name': 'connect_fattura24', 'arguments': {}})
                assert ready['structuredContent']['state'] == 'ready'
                assert ready['structuredContent']['authorization_url'] is None
                assert os.stat(storage.path).st_mode & 0o777 == 0o600
                # Storage survives a new connection object and never exposes tokens in status.
                restored = OfficialConnection(PrivateOAuthStorage(storage.path), httpx.MockTransport(fake))
                assert (await restored.list_tools())[0].model_dump() == Tool.model_validate(TOOL).model_dump()
                assert 'demo-official-token' not in json.dumps(await connection.status())
                headers = {**auth, 'Accept': 'application/json, text/event-stream', 'MCP-Protocol-Version': '2025-03-26'}
                async def rpc(method, params=None):
                    payload = {'jsonrpc': '2.0', 'id': 1, 'method': method}
                    if params is not None:
                        payload['params'] = params
                    r = await client.post('/mcp', headers=headers, json=payload)
                    assert r.status_code == 200, r.text
                    if r.headers.get("Mcp-Session-Id"):
                        headers["Mcp-Session-Id"] = r.headers["Mcp-Session-Id"]
                    return r.json()['result']
                await rpc('initialize', {'protocolVersion': '2025-03-26', 'capabilities': {}, 'clientInfo': {'name': 'demo', 'version': '1'}})
                listing = await rpc('tools/list', {})
                tools = {t['name']: t for t in listing['tools']}
                assert 'prepare_invoice' in tools and 'report_bilancino' in tools
                assert tools['report_bilancino']['inputSchema'] == TOOL['inputSchema']
                assert 'segnala_limite_connettore' not in tools
                result = await rpc('tools/call', {'name': 'report_bilancino', 'arguments': {'anno': 2026}})
                assert result == RESULT
                fake.result = {'content': [{'type': 'text', 'text': 'Demo provider error'}], 'isError': True}
                error_result = await rpc('tools/call', {'name': 'report_bilancino', 'arguments': {'anno': 2026}})
                assert error_result['isError'] is True and error_result['content'] == fake.result['content']
                calls = sum(m['method'] == 'tools/call' for m in fake.messages)
                invalid = await rpc('tools/call', {'name': 'report_bilancino', 'arguments': {'anno': 'invalid'}})
                assert invalid['isError'] is True
                assert sum(m['method'] == 'tools/call' for m in fake.messages) == calls
                bad = await rpc('tools/call', {'name': 'segnala_limite_connettore', 'arguments': {}})
                assert bad['isError'] is True
                assert not any(m.get('params', {}).get('name') == 'segnala_limite_connettore' for m in fake.messages)
                storage.update(expires_at=time.time() - 10)
                renewed = OfficialConnection(PrivateOAuthStorage(storage.path), httpx.MockTransport(fake))
                assert (await renewed.list_tools())[0].name == 'report_bilancino'
                assert fake.refreshed
                assert (await storage.get_tokens()).access_token == 'demo-refreshed-token'
    asyncio.run(run())


def test_disconnected_does_not_contact_provider(tmp_path):
    async def run():
        def forbidden(req):
            raise AssertionError('Network attempted without OAuth')
        connection = OfficialConnection(PrivateOAuthStorage(tmp_path / 'missing.json'), httpx.MockTransport(forbidden))
        assert await connection.list_tools() == []
        assert (await connection.status())['credentials_stored'] is False
        try:
            await connection.call_tool('report_bilancino', {'anno': 2026})
        except RuntimeError as exc:
            assert 'non collegato' in str(exc)
        else:
            raise AssertionError('Unauthenticated tool call accepted')
    asyncio.run(run())
