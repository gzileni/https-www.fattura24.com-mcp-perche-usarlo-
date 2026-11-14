"""Additional documented REST functions. Single-user local service only.

Source: https://www.fattura24.com/api/verifica/
        https://www.fattura24.com/api/crea-contatto/
        https://www.fattura24.com/api/download-pdf/
Do not expose this service on the public Internet.
"""
import base64
import hashlib
import os
import urllib.parse
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from pydantic import BaseModel, Field
from fattura24_client import configured, _connect, _LOCK, _CONFIRM

ROOT = "https://www.app.fattura24.com/api/v0.3/"
MAX_PDF_BYTES = 8 * 1024 * 1024

class Customer(BaseModel):
    name: str = Field(min_length=1)
    address: str = Field(min_length=1)
    postcode: str = Field(min_length=3)
    city: str = Field(min_length=1)
    province: str = Field(default="")
    country: str = "IT"
    vat_code: str = ""
    fiscal_code: str = ""
    email: str = ""
    pec: str = ""
    destination_code: str = ""

def customer_xml(customer: Customer) -> str:
    if not (customer.vat_code or customer.fiscal_code):
        raise ValueError("Per la modifica sicura di una anagrafica serve P.IVA o codice fiscale")
    root = ET.Element("Fattura24")
    document = ET.SubElement(root, "Document")
    tags = {
        "CustomerName": customer.name,
        "CustomerAddress": customer.address,
        "CustomerPostcode": customer.postcode,
        "CustomerCity": customer.city,
        "CustomerProvince": customer.province,
        "CustomerCountry": customer.country,
        "CustomerVatCode": customer.vat_code,
        "CustomerFiscalCode": customer.fiscal_code,
        "CustomerEmail": customer.email,
        "FeCustomerPec": customer.pec,
        "FeDestinationCode": customer.destination_code,
    }
    for tag, value in tags.items():
        ET.SubElement(document, tag).text = value
    return ET.tostring(root, encoding="unicode")

def _post(endpoint: str, fields: dict, max_bytes: int = 128 * 1024) -> bytes:
    if not os.getenv("FATTURA24_API_KEY"):
        raise RuntimeError("FATTURA24_API_KEY non impostata nel file .env locale")
    params = {"apiKey": os.environ["FATTURA24_API_KEY"], **fields}
    encoded = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(ROOT + endpoint, data=encoded, method="POST",
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=25) as response:
        data = response.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ValueError("Risposta troppo grande")
    return data

def test_key_once() -> dict:
    """Call only on explicit request. Provider says TestKey is NOT a health probe."""
    with _LOCK:
        try:
            root = ET.fromstring(_post("TestKey", {}))
        except (OSError, urllib.error.URLError, ET.ParseError):
            return {"valid": "unknown", "note": "Esito incerto: controlla manualmente le impostazioni Fattura24"}
    code = root.findtext(".//returnCode")
    return {"valid": code == "1", "provider_code": code,
            "note": "Verifica della chiave richiesta dall'utente. Non usare per monitoraggio periodico."}

def save_customer(customer: Customer, request_id: str, confirmation: str) -> dict:
    """May also UPDATE an existing Fattura24 customer; requires special consent."""
    if not configured():
        raise RuntimeError("Scrittura disabilitata")
    if confirmation != "CONFERMO CREAZIONE O AGGIORNAMENTO CLIENTE":
        raise ValueError("Conferma cliente mancante")
    if not request_id or len(request_id)>100 or not all(c.isalnum() or c in "_-" for c in request_id):
        raise ValueError("request_id unico richiesto")
    xml_payload = customer_xml(customer)
    digest = hashlib.sha256(xml_payload.encode()).hexdigest()
    with _LOCK:
        conn = _connect()
        try:
            row = conn.execute("SELECT digest,status,doc_id FROM submissions WHERE request_id=?", (request_id,)).fetchone()
            if row:
                if row[0] != digest: raise ValueError("request_id riutilizzato con contenuto diverso")
                return {"status": row[1], "existing_response": True, "note": "Nessuna nuova chiamata eseguita"}
            conn.execute("INSERT INTO submissions (request_id,digest,status) VALUES(?,?,?)", (request_id,digest,"uncertain"))
            try:
                data = _post("SaveCustomer", {"xml": xml_payload})
                root = ET.fromstring(data)
            except (OSError, urllib.error.URLError, ET.ParseError, ValueError):
                return {"status": "uncertain", "note": "Esito incerto; verificare la rubrica prima di riprovare"}
            code = root.findtext(".//returnCode")
            if code == "0":
                conn.execute("UPDATE submissions SET status='saved' WHERE request_id=?", (request_id,))
                return {"status": "saved_or_updated", "note": "Controllare la rubrica Fattura24"}
            return {"status": "uncertain", "provider_code": code,
                    "note": "Verifica manuale necessaria; nessun tentativo automatico"}
        finally:
            conn.close()

def get_pdf(doc_id: str) -> dict:
    """Read a PDF already generated by the user's own Fattura24 account."""
    if not doc_id.isdecimal() or len(doc_id)>20:
        raise ValueError("doc_id numerico richiesto")
    with _LOCK:
        try:
            payload = _post("GetFile", {"docId": doc_id}, max_bytes=MAX_PDF_BYTES)
        except (OSError, urllib.error.URLError, ValueError):
            return {"status": "error", "note": "Download non riuscito. Verifica il documento in Fattura24."}
    if not payload.startswith(b"%PDF-"):
        return {"status": "error", "note": "Fattura24 non ha restituito un PDF valido. Nessun file salvato."}
    return {"status": "pdf_ready", "doc_id": doc_id, "mime_type": "application/pdf",
            "bytes": len(payload), "base64": base64.b64encode(payload).decode("ascii"),
            "warning": "Contiene dati del cliente: trattare come documento riservato."}
