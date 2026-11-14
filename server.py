"""Local MCP preview server. No REST writes; no Docker process management."""
import hmac
import json
import os
from mcp.server.fastmcp import FastMCP
from starlette.responses import PlainTextResponse
from core import Document, preview, make_xml, fattura24_xml
from fattura24_client import configured, register_invoice
from fattura24_extra import Customer, customer_xml, test_key_once, save_customer, get_pdf

mcp = FastMCP("Fattura24 Preview Bridge", stateless_http=True, json_response=True)

@mcp.tool()
def bridge_status() -> dict:
    """Report actual preview-only capabilities; no credentials exposed."""
    return {
        "status": "ready",
        "mode": "preview_only",
        "tools": ["bridge_status", "prepare_invoice", "invoice_xml_preview", "prepare_ddt_notes", "invoice_api_payload_preview", "save_invoice_to_fattura24", "verify_fattura24_api_key", "customer_payload_preview", "save_customer_to_fattura24", "download_document_pdf"],
        "writes_enabled": configured(),
        "writes_require_explicit_confirmation": True,
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

@mcp.tool()
def invoice_api_payload_preview(payload_json: str) -> dict:
    """Generate Fattura24 SaveDocument payload preview; no API call."""
    doc = Document.model_validate(json.loads(payload_json))
    return {"preview": preview(doc), "save_document_xml": fattura24_xml(doc), "warning": "Verificare i campi e il regime fiscale; solo fatture semplici."}

@mcp.tool()
def save_invoice_to_fattura24(payload_json: str, request_id: str, confirmation: str) -> dict:
    """SAVE AN ACTUAL INVOICE in Fattura24 using its official SaveDocument endpoint.

    Use ONLY after the human saw the exact preview and explicitly requested the
    save. Ask them to confirm with phrase CONFERMO IL SALVATAGGIO IN FATTURA24.
    Never call autonomously, for testing, or retry after timeout. Requires
    FATTURA24_ENABLE_WRITES=true and a private local API key. Does NOT send SdI.
    """
    doc = Document.model_validate(json.loads(payload_json))
    return register_invoice(doc, request_id=request_id, confirmation=confirmation)

@mcp.tool()
def verify_fattura24_api_key() -> dict:
    """Verify a configured API key ONCE, only after explicit user request. Not a health check."""
    return test_key_once()

@mcp.tool()
def customer_payload_preview(payload_json: str) -> dict:
    """Show XML prior to any possible customer create/update."""
    customer = Customer.model_validate(json.loads(payload_json))
    return {"xml": customer_xml(customer),
            "warning": "SaveCustomer aggiorna anche clienti esistenti con stessa P.IVA/CF/nome!"}

@mcp.tool()
def save_customer_to_fattura24(payload_json: str, request_id: str, confirmation: str) -> dict:
    """CREATES OR UPDATES a real customer. Preview + explicit human confirmation required.

    User must type CONFERMO CREAZIONE O AGGIORNAMENTO CLIENTE after reviewing.
    Requires local API key, writes enabled, and unique request_id. No blind retry.
    """
    customer = Customer.model_validate(json.loads(payload_json))
    return save_customer(customer, request_id, confirmation)

@mcp.tool()
def download_document_pdf(doc_id: str) -> dict:
    """Retrieve a PDF from user's Fattura24 account. Contains sensitive data.

    Requires local FATTURA24_API_KEY. Returned base64 can be large; avoid
    calling when the user only needs an invoice summary.
    """
    return get_pdf(doc_id)

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
