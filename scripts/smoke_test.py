#!/usr/bin/env python3
"""Local end-to-end smoke test. Never calls Fattura24 or saves documents.

Example:
  python scripts/smoke_test.py
Reads BRIDGE_TOKEN from environment, otherwise from local .env (not printed).
"""
import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request

BASE = os.getenv("BRIDGE_URL", "http://127.0.0.1:8765").rstrip("/")
TOKEN = os.getenv("BRIDGE_TOKEN", "")

def local_token():
    if TOKEN:
        return TOKEN
    env_file = Path(__file__).resolve().parents[1] / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8-sig").splitlines():
            if line.startswith("BRIDGE_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("Token BRIDGE_TOKEN mancante. Esegui prima lo script di avvio.")

def request(method, path, data=None, headers=None, timeout=10):
    body = json.dumps(data).encode() if data is not None else None
    h = dict(headers or {})
    if body is not None:
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=body, headers=h, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw = response.read()
        return response.status, json.loads(raw) if raw and body is not None else raw.decode()

def rpc(token, method, params=None, rpc_id=1):
    data = {"jsonrpc":"2.0", "method":method, "id":rpc_id}
    if params is not None:
        data["params"] = params
    status, response = request(
        "POST", "/mcp", data,
        {"Authorization": "Bearer " + token,
         "Accept": "application/json, text/event-stream",
         "MCP-Protocol-Version": "2025-03-26"},
    )
    assert status == 200, status
    if isinstance(response, str):
        raise RuntimeError("Unexpected non-JSON MCP reply. Check SDK/server compatibility.")
    if "error" in response:
        raise RuntimeError(f"RPC error: {response['error']}")
    return response["result"]

def main():
    token = local_token()
    for i in range(20):
        try:
            status, health = request("GET", "/health")
            assert status == 200 and health == "ok"
            break
        except (urllib.error.URLError, AssertionError):
            if i == 19:
                raise RuntimeError("Il container non risponde a /health. Esegui docker compose logs --tail=100")
            time.sleep(2)
    print("[OK] HTTP /health")
    try:
        request("POST", "/mcp", {"jsonrpc":"2.0","id":0,"method":"ping"},
                {"Accept":"application/json, text/event-stream"})
        raise RuntimeError("MCP senza autenticazione: controllo sicurezza FALLITO")
    except urllib.error.HTTPError as err:
        if err.code != 401:
            raise
    print("[OK] Accesso MCP senza token rifiutato (401)")

    init = rpc(token, "initialize", {
        "protocolVersion":"2025-03-26",
        "capabilities":{},
        "clientInfo":{"name":"fattura24-smoke-test","version":"0.1"}
    })
    assert "serverInfo" in init
    tools = rpc(token, "tools/list", {}, 2)["tools"]
    names = {tool["name"] for tool in tools}
    for name in ("bridge_status","prepare_invoice","prepare_ddt_notes"):
        assert name in names, f"Tool MCP mancante: {name}"
    print("[OK] MCP initialize + tools/list")

    status = rpc(token, "tools/call", {"name":"bridge_status", "arguments":{}}, 3)
    assert not status.get("isError"), status
    print("[OK] Tool bridge_status")
    payload = json.dumps({
        "customer_name":"Solo test — nessuna fattura registrata",
        "rows":[{"description":"Articolo dimostrativo","quantity":"2",
                 "price_net":"10.00","vat_code":"22","vat_description":"22%"}]
    })
    result = rpc(token, "tools/call", {
        "name":"prepare_invoice","arguments":{"payload_json":payload}
    }, 4)
    assert not result.get("isError"), result
    text = json.dumps(result, ensure_ascii=False)
    assert "24.40" in text, text
    print("[OK] Tool prepare_invoice (totale atteso 24.40)")
    print("\nTUTTI I CONTROLLI SUPERATI — nessuna API Fattura24 chiamata.")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[ERRORE] {exc}", file=sys.stderr)
        sys.exit(1)
