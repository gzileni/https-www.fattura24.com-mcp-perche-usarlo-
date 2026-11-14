#!/usr/bin/env python3
"""No-write MCP integration test, runnable inside the image with stdlib only.

Never calls tools that access Fattura24, even if the instance has an API key.
Usage: docker exec fattura24-mcp python /app/smoke_test.py
Outside Docker: BRIDGE_TOKEN=... python scripts/smoke_test.py
"""
import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

BASE = os.getenv("BRIDGE_URL", "http://127.0.0.1:8765").rstrip("/")
PROTOCOL = "2025-03-26"
SAFE_TOOLS = {
    "bridge_status", "prepare_invoice", "invoice_xml_preview",
    "prepare_ddt_notes", "invoice_api_payload_preview", "customer_payload_preview",
}
EXTERNAL_TOOLS = {
    "save_invoice_to_fattura24", "save_customer_to_fattura24",
    "verify_fattura24_api_key", "download_document_pdf",
}


def check(condition, message):
    if not condition:
        raise RuntimeError(message)


def local_token():
    if os.getenv("BRIDGE_TOKEN"):
        return os.environ["BRIDGE_TOKEN"]
    env_file = Path(os.getenv("BRIDGE_ENV_FILE", str(Path(__file__).resolve().parents[1] / ".env")))
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8-sig").splitlines():
            if line.startswith("BRIDGE_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("Token mancante. Usare docker exec fattura24-mcp python /app/smoke_test.py oppure BRIDGE_ENV_FILE.")


def request(method, path, data=None, headers=None, timeout=10):
    body = json.dumps(data).encode() if data is not None else None
    h = dict(headers or {})
    if body is not None:
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=body, headers=h, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw = response.read()
        return response.status, json.loads(raw) if raw and body is not None else raw.decode()


def headers(token):
    return {"Authorization": "Bearer " + token,
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": PROTOCOL}


def rpc(token, method, params=None, rpc_id=1):
    data = {"jsonrpc": "2.0", "method": method, "id": rpc_id}
    if params is not None:
        data["params"] = params
    status, response = request("POST", "/mcp", data, headers(token))
    check(status == 200 and isinstance(response, dict), "Risposta MCP non JSON/200")
    check(response.get("id") == rpc_id, "ID JSON-RPC non corrispondente")
    check("error" not in response, "Errore JSON-RPC durante " + method)
    return response["result"]


def call(token, name, arguments, expect_error=False):
    # An explicit allowlist prevents accidental provider calls from this test.
    check(name in SAFE_TOOLS or name == "nonexistent_demo_tool", "Tool non ammesso nel test")
    result = rpc(token, "tools/call", {"name": name, "arguments": arguments})
    check(bool(result.get("isError")) == expect_error, "Esito inatteso per " + name)
    if expect_error:
        return result
    if "structuredContent" in result:
        return result["structuredContent"]
    text = "".join(block.get("text", "") for block in result.get("content", []) if block["type"] == "text")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def main():
    global PROTOCOL
    token = local_token()
    for attempt in range(20):
        try:
            status, health = request("GET", "/health")
            check(status == 200 and health == "ok", "Health non valido")
            break
        except (OSError, RuntimeError):
            if attempt == 19:
                raise RuntimeError("/health non raggiungibile; controllare i log del container") from None
            time.sleep(1)
    print("[OK] HTTP /health")
    for label, auth in (("assente", {}), ("errato", {"Authorization": "Bearer invalid-demo-token"})):
        try:
            request("POST", "/mcp", {"jsonrpc": "2.0", "id": 0, "method": "ping"},
                    {"Accept": "application/json, text/event-stream", **auth})
        except urllib.error.HTTPError as err:
            check(err.code == 401, "Atteso 401 per token " + label)
        else:
            raise RuntimeError("Autenticazione accettata con token " + label)
        print("[OK] Token " + label + " rifiutato (401)")

    init = rpc(token, "initialize", {"protocolVersion": PROTOCOL, "capabilities": {},
               "clientInfo": {"name": "fattura24-smoke-test", "version": "0.2"}})
    check("serverInfo" in init and "tools" in init["capabilities"], "Capacita MCP mancanti")
    PROTOCOL = init["protocolVersion"]
    status, _ = request("POST", "/mcp", {"jsonrpc": "2.0", "method": "notifications/initialized"}, headers(token))
    check(status == 202, "Notifica initialized non accettata")
    print("[OK] MCP initialize + notifications/initialized; protocol=" + PROTOCOL)
    tools = rpc(token, "tools/list", {})["tools"]
    names = {tool["name"] for tool in tools}
    check(SAFE_TOOLS | EXTERNAL_TOOLS == names, "Elenco tool inatteso: " + str(sorted(names)))
    check(all(tool.get("inputSchema", {}).get("type") == "object" for tool in tools), "Schema tool mancante")
    print("[OK] tools/list: 10 strumenti con schema")

    state = call(token, "bridge_status", {})
    check(state["writes_enabled"] is False, "Test interrotto: scritture abilitate sull'istanza")
    check(set(state["tools"]) == names, "bridge_status non allineato a tools/list")
    check(state["sdi_transmission_enabled"] is False and state["ddt_registration_enabled"] is False,
          "Capacita non previste abilitate")
    print("[OK] bridge_status: scritture/SdI/DDT disabilitati")
    payload = json.dumps({
        "customer_name": "DEMO & TEST - nessun documento reale",
        "customer_address": "Via Dimostrativa 1", "customer_postcode": "00000",
        "customer_city": "Citta Demo", "customer_vat_code": "00000000000", "destination_code": "0000000",
        "rows": [{"description": "Articolo <demo>", "quantity": "2", "price_net": "10.00", "vat_code": "22"}],
    })
    args = {"payload_json": payload}
    result = call(token, "prepare_invoice", args)
    check((result["net"], result["vat"], result["total"], result["state"]) ==
          ("20.00", "4.40", "24.40", "preview_only"), "Importi demo errati")
    print("[OK] prepare_invoice: 20.00 + 4.40 = 24.40")
    xml = call(token, "invoice_xml_preview", args)
    # FastMCP may wrap primitive return values in structuredContent.result.
    if isinstance(xml, dict):
        xml = xml["result"]
    root = ET.fromstring(xml)
    check(root.tag == "DraftPreview" and root.findtext("Customer") == "DEMO & TEST - nessun documento reale",
          "XML anteprima o escaping errati")
    print("[OK] invoice_xml_preview: XML e escaping")
    api = call(token, "invoice_api_payload_preview", args)
    check(ET.fromstring(api["save_document_xml"]).findtext("./Document/Total") == "24.40", "XML payload errato")
    print("[OK] invoice_api_payload_preview: XML locale, nessun invio")
    ddt = call(token, "prepare_ddt_notes", {"customer": "Cliente Demo", "goods": "Articolo Demo",
               "destination": "Destinazione Demo", "transport": "Trasporto Demo"})
    check(ddt["status"] == "notes_only", "DDT non in modalita note")
    print("[OK] prepare_ddt_notes: sole note")
    customer = call(token, "customer_payload_preview", {"payload_json": json.dumps({
        "name": "Cliente Demo", "address": "Via Demo 1", "postcode": "00000",
        "city": "Citta Demo", "vat_code": "00000000000"})})
    check(ET.fromstring(customer["xml"]).findtext("./Document/CustomerName") == "Cliente Demo", "XML cliente errato")
    print("[OK] customer_payload_preview: XML locale, nessun aggiornamento")
    call(token, "prepare_invoice", {"payload_json": '{"customer_name":"DEMO","rows":[]}'}, expect_error=True)
    call(token, "nonexistent_demo_tool", {}, expect_error=True)
    print("[OK] Payload non valido e tool inesistente restituiscono isError")
    print("TUTTI I CONTROLLI SUPERATI: 6 tool locali; nessuna API Fattura24 chiamata.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("[ERRORE] " + str(exc), file=sys.stderr)
        sys.exit(1)
