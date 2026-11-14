"""Local MCP preview server. No REST writes; no Docker process management."""
import hmac
import json
import os
from mcp.server.fastmcp import FastMCP
from starlette.responses import PlainTextResponse
from core import Document, preview, make_xml

mcp = FastMCP("Fattura24 Preview Bridge", stateless_http=True, json_response=True)

@mcp.tool()
def bridge_status() -> dict:
    """Report actual preview-only capabilities; no credentials exposed."""
    return {
        "status": "ready",
        "mode": "preview_only",
        "tools": ["bridge_status", "prepare_invoice", "invoice_xml_preview", "prepare_ddt_notes"],
        "writes_enabled": False,
        "ddt_registration_enabled": False,
        "sdi_transmission_enabled": False,
    }

@mcp.tool()
def prepare_invoice(payload_json: str) -> dict:
    """Validate illustrative JSON and calculate preview totals without saving."""
    doc = Document.model_validate(json.loads(payload_json))
    return preview(doc)

@mcp.tool()
def invoice_xml_preview(payload_json: str) -> str:
    """Create illustrative draft XML; it is not FatturaPA nor Fattura24 SaveDocument XML."""
    doc = Document.model_validate(json.loads(payload_json))
    return make_xml(doc)

@mcp.tool()
def prepare_ddt_notes(customer: str, goods: str, destination: str, transport: str) -> dict:
    """Gather DDT notes; no DDT is created in Fattura24."""
    return {
        "customer": customer, "goods": goods,
        "destination": destination, "transport": transport,
        "status": "notes_only",
        "next_step": "Verificare e inserire i dati nell'interfaccia ufficiale Fattura24.",
    }

@mcp.custom_route("/health", methods=["GET"])
async def health(request):
    return PlainTextResponse("ok")

backend = mcp.streamable_http_app()

class BearerGuard:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] in {"http", "websocket"} and scope.get("path", "").startswith("/mcp"):
            headers = dict(scope.get("headers", []))
            actual = headers.get(b"authorization", b"").decode(errors="ignore")
            expected = os.environ.get("BRIDGE_TOKEN", "")
            if not expected or not hmac.compare_digest(actual, f"Bearer {expected}"):
                return await PlainTextResponse("Unauthorized", status_code=401)(scope, receive, send)
        return await self.app(scope, receive, send)

app = BearerGuard(backend)
