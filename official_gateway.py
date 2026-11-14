"""Official-tool federation for the single-user MCP bridge.

The local client authenticates with BRIDGE_TOKEN. This process is a separate OAuth
client of Fattura24; official tokens are never accepted from or returned to the
local MCP client. Tool schemas/results come from live official MCP discovery.
"""
import asyncio
from contextlib import asynccontextmanager
import hmac
import json
import os
from pathlib import Path
import secrets
import time
from urllib.parse import parse_qs, urlsplit

import httpx
from mcp import ClientSession
from mcp.client.auth import OAuthClientProvider
from mcp.client.streamable_http import streamable_http_client
from mcp.shared.auth import OAuthClientInformationFull, OAuthClientMetadata, OAuthToken, OAuthMetadata
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse

OFFICIAL_MCP = "https://www.app.fattura24.com/mcp"
READ_TOOLS = frozenset({
    "ricerca_documenti", "ricerca_esito_sdi", "download_esito_sdi",
    "report_fatturato", "report_fatturato_confronto", "report_pagamenti_confronto",
    "report_prodotti_servizi", "report_area_geografica", "report_analisi_iva",
    "report_bilancino", "report_forecast", "report_pareto", "report_churn_rate",
    "account_dettagli", "account_consumi_mcp",
})


def public_base():
    base = os.getenv("BRIDGE_PUBLIC_URL", "http://127.0.0.1:8765").rstrip("/")
    parsed = urlsplit(base)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.path or parsed.query or parsed.fragment or parsed.username:
        raise ValueError("BRIDGE_PUBLIC_URL deve essere una origine senza percorso o credenziali")
    if parsed.scheme != "https" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("HTTP consentito soltanto su loopback")
    return base


class PrivateOAuthStorage:
    """Atomic 0600 storage in the existing private Docker volume; no API keys."""
    def __init__(self, path=None):
        self.path = Path(path or os.getenv("FATTURA24_OAUTH_FILE", "/data/official-oauth.json"))

    def read(self):
        try:
            data = json.loads(self.path.read_text())
        except FileNotFoundError:
            return {}
        # OAuth registrations are bound to the exact gateway callback origin.
        if data.get("callback") != public_base() + "/oauth/callback":
            return {}
        return data

    def update(self, **values):
        data = {**self.read(), **values, "callback": public_base() + "/oauth/callback"}
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        temporary = self.path.with_name(self.path.name + "." + secrets.token_hex(8))
        try:
            fd = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, "w") as handle:
                json.dump(data, handle)
            os.replace(temporary, self.path)
        finally:
            temporary.unlink(missing_ok=True)

    async def get_tokens(self):
        data = self.read()
        if "tokens" not in data:
            return None
        token = OAuthToken.model_validate(data["tokens"])
        if data.get("expires_at") is not None:
            token.expires_in = max(0, int(data["expires_at"] - time.time()))
        return token

    async def set_tokens(self, tokens):
        self.update(tokens=tokens.model_dump(mode="json"), expires_at=(time.time() + tokens.expires_in) if tokens.expires_in is not None else None)

    async def get_client_info(self):
        info = self.read().get("client_info")
        return OAuthClientInformationFull.model_validate(info) if info else None

    async def set_client_info(self, client_info):
        self.update(client_info=client_info.model_dump(mode="json"))


class PersistentOAuthProvider(OAuthClientProvider):
    async def _initialize(self):
        await super()._initialize()
        # SDK 1.29 restores tokens but not their absolute expiry or discovered
        # token endpoint. Restore both to permit refresh after container restart.
        self.context.token_expiry_time = self.context.storage.read().get("expires_at")
        self.context.oauth_metadata = OAuthMetadata(
            issuer="https://www.app.fattura24.com",
            authorization_endpoint="https://www.app.fattura24.com/oauth/authorize",
            token_endpoint="https://www.app.fattura24.com/oauth/token",
            registration_endpoint="https://www.app.fattura24.com/oauth/register",
            response_types_supported=["code"], code_challenge_methods_supported=["S256"])


class OfficialConnection:
    def __init__(self, storage=None, transport=None):
        self.storage = storage or PrivateOAuthStorage()
        self.transport = transport  # Only tests inject a transport; upstream URL is fixed.
        self.lock = asyncio.Lock()
        self.tools = []
        self.state = "not_connected"
        self.authorization_url = None
        self.callback = None
        self.login_task = None
        self.login_id = None
        self.login_ready = None

    async def status(self):
        return {"state": self.state, "credentials_stored": bool(await self.storage.get_tokens()),
                "tool_names": [t.name for t in self.tools], "upstream": OFFICIAL_MCP}

    async def _redirect(self, url):
        if self.callback is None:
            raise RuntimeError("OAuth richiesto: chiama connect_fattura24 nella chat")
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.netloc != "www.app.fattura24.com" or parsed.path != "/oauth/authorize":
            raise RuntimeError("Endpoint OAuth inatteso")
        self.authorization_url = url
        self.state = "awaiting_authorization"
        self.login_ready.set()

    async def _callback(self):
        if self.callback is None:
            raise RuntimeError("Collegamento OAuth non avviato")
        return await asyncio.wait_for(asyncio.shield(self.callback), timeout=300)

    @asynccontextmanager
    async def session(self):
        auth = PersistentOAuthProvider(server_url=OFFICIAL_MCP, storage=self.storage,
            client_metadata=OAuthClientMetadata(
                client_name="Fattura24 MCP Bridge (istanza personale)",
                redirect_uris=[public_base() + "/oauth/callback"],
                grant_types=["authorization_code", "refresh_token"],
                response_types=["code"], token_endpoint_auth_method="none", scope="mcp"),
            redirect_handler=self._redirect, callback_handler=self._callback, timeout=300)
        async with httpx.AsyncClient(auth=auth, transport=self.transport, follow_redirects=False,
                                     timeout=httpx.Timeout(60, connect=10)) as http:
            async with streamable_http_client(OFFICIAL_MCP, http_client=http) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    yield session

    async def _discover(self, session):
        result, cursor, seen = [], None, set()
        while True:
            page = await session.list_tools(cursor=cursor)
            for tool in page.tools:
                # Only documented read tools, further constrained by live annotations.
                if tool.name in READ_TOOLS and tool.annotations and tool.annotations.readOnlyHint is True and tool.annotations.destructiveHint is False:
                    result.append(tool)
            cursor = page.nextCursor
            if not cursor:
                break
            if cursor in seen:
                raise RuntimeError("Paginazione MCP non valida")
            seen.add(cursor)
        self.tools = result
        self.state = "ready"
        return result

    async def list_tools(self):
        # Discovery must never start an interactive login or use fake schemas.
        if self.login_task and not self.login_task.done():
            return self.tools
        if not await self.storage.get_tokens():
            return []
        async with self.lock:
            try:
                async with self.session() as session:
                    return await self._discover(session)
            except Exception:
                self.tools = []
                self.state = "authorization_or_connection_required"
                return []

    async def call_tool(self, name, arguments):
        if name not in READ_TOOLS:
            raise ValueError("Tool ufficiale non consentito: gateway in sola lettura")
        if not await self.storage.get_tokens():
            raise RuntimeError("Fattura24 non collegato: chiama connect_fattura24 nella chat")
        if self.login_task and not self.login_task.done():
            raise RuntimeError("Autorizzazione Fattura24 in corso")
        async with self.lock:
            try:
                async with self.session() as session:
                    tools = await self._discover(session)
                    if name not in {t.name for t in tools}:
                        raise RuntimeError("Tool non disponibile nell'account ufficiale")
                    # Exact original name, arguments, result, errors and content blocks.
                    return await session.call_tool(name, arguments)
            except Exception:
                self.state = "authorization_or_connection_required"
                raise RuntimeError("Chiamata MCP ufficiale non riuscita; verificare collegamento e autorizzazione") from None

    async def start_login(self):
        if self.state == "ready" and await self.storage.get_tokens():
            return {**await self.status(), "authorization_url": None}
        if not self.login_task or self.login_task.done():
            self.login_id = secrets.token_urlsafe(16)
            self.callback = asyncio.get_running_loop().create_future()
            self.login_ready = asyncio.Event()
            self.authorization_url = None
            self.state = "connecting"
            self.login_task = asyncio.create_task(self._login())
        try:
            await asyncio.wait_for(self.login_ready.wait(), timeout=15)
        except asyncio.TimeoutError:
            pass
        return {**await self.status(), "authorization_url": self.authorization_url}

    async def _login(self):
        try:
            async with self.lock:
                async with self.session() as session:
                    await self._discover(session)
        except Exception:
            self.state = "authorization_or_connection_required"
        finally:
            self.authorization_url = None
            self.login_ready.set()
            if self.callback and not self.callback.done():
                self.callback.cancel()
            self.callback = None

    def accept_callback(self, code, state, error=None):
        if not self.callback or self.callback.done() or not self.authorization_url:
            return False
        expected = parse_qs(urlsplit(self.authorization_url).query).get("state", [""])[0]
        if not state or not expected or not hmac.compare_digest(state, expected):
            return False
        if error:
            self.callback.set_exception(RuntimeError("Autorizzazione negata"))
            return True
        if not code:
            return False
        self.callback.set_result((code, state))
        return True


class ConnectionRoutes:
    """OAuth setup endpoints only. All tools remain at the sole /mcp endpoint."""
    def __init__(self, fallback, connection):
        self.fallback, self.connection = fallback, connection

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("path") not in {"/official/connect", "/official/status", "/oauth/callback"}:
            return await self.fallback(scope, receive, send)
        request = Request(scope, receive)
        if request.url.path == "/oauth/callback":
            params = dict(request.query_params)
            # Avoid authorization codes appearing in Uvicorn access logs.
            scope["query_string"] = b""
            valid = request.method == "GET" and self.connection.accept_callback(params.get("code"), params.get("state"), params.get("error"))
            response = PlainTextResponse("Autorizzazione ricevuta. Torna al client locale." if valid else "Callback OAuth non valido o scaduto", status_code=200 if valid else 400)
        else:
            expected = os.getenv("BRIDGE_TOKEN", "")
            actual = request.headers.get("authorization", "")
            if not expected or not hmac.compare_digest(actual.encode(), ("Bearer " + expected).encode()):
                response = PlainTextResponse("Unauthorized", status_code=401)
            elif request.url.path == "/official/connect" and request.method == "POST":
                response = JSONResponse(await self.connection.start_login())
            elif request.url.path == "/official/status" and request.method == "GET":
                response = JSONResponse({**await self.connection.status(), "authorization_url": self.connection.authorization_url})
            else:
                response = PlainTextResponse("Method not allowed", status_code=405)
        response.headers["Cache-Control"] = "no-store"
        await response(scope, receive, send)
