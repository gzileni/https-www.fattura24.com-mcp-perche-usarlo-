"""Fattura24 official SaveDocument integration. User-controlled instance only.

This is NOT a complete invoicing or tax compliance engine. No blind retries.
"""
import hashlib
import os
import sqlite3
import threading
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from core import Document, fattura24_xml, preview

_ENDPOINT = "https://www.app.fattura24.com/api/v0.3/SaveDocument"
_LOCK = threading.Lock()
_DB_PATH = os.getenv("BRIDGE_DB_PATH", "/data/submissions.sqlite3")
_CONFIRM = "CONFERMO IL SALVATAGGIO IN FATTURA24"

def configured():
    return bool(os.getenv("FATTURA24_API_KEY")) and os.getenv("FATTURA24_ENABLE_WRITES") == "true"

def _connect():
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(_DB_PATH, timeout=30, isolation_level=None)
    conn.execute("""CREATE TABLE IF NOT EXISTS submissions (
        request_id TEXT PRIMARY KEY, digest TEXT NOT NULL,
        status TEXT NOT NULL, doc_id TEXT, doc_number TEXT
    )""")
    return conn

def register_invoice(doc: Document, request_id: str, confirmation: str) -> dict:
    """Actual write: only upon opt-in, explicit confirmation and unique request ID.

    Failed/uncertain requests are never replayed automatically. Inspect Fattura24
    before deciding on another attempt with a new request ID.
    """
    if not configured():
        raise RuntimeError("Scrittura disabilitata: configurare FATTURA24_API_KEY e FATTURA24_ENABLE_WRITES=true")
    if confirmation != _CONFIRM:
        raise ValueError("Conferma obbligatoria: riporta esattamente la frase di conferma dopo aver esaminato i dati")
    if not request_id or len(request_id) > 100 or not all(ch.isalnum() or ch in "-_" for ch in request_id):
        raise ValueError("request_id unico richiesto: lettere, numeri, trattino e underscore")
    xml_payload = fattura24_xml(doc)
    digest = hashlib.sha256(xml_payload.encode("utf-8")).hexdigest()
    with _LOCK:
        conn = _connect()
        try:
            row = conn.execute("SELECT digest,status,doc_id,doc_number FROM submissions WHERE request_id=?", (request_id,)).fetchone()
            if row:
                if row[0] != digest:
                    raise ValueError("request_id gia usato per un documento differente")
                return {
                    "status": row[1],
                    "document_id": row[2],
                    "document_number": row[3],
                    "replayed": False,
                    "note": "Nessuna nuova chiamata effettuata. Se esito incerto, controlla Fattura24 manualmente.",
                }
            conn.execute("INSERT INTO submissions (request_id,digest,status) VALUES (?,?,?)", (request_id,digest,"uncertain"))
            body = urllib.parse.urlencode({"apiKey": os.environ["FATTURA24_API_KEY"], "xml": xml_payload}).encode("utf-8")
            req = urllib.request.Request(_ENDPOINT, body, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
            # Avoid automatic retries: a timeout could mean the invoice was saved.
            try:
                with urllib.request.urlopen(req, timeout=25) as response:
                    data = response.read(128 * 1024)
            except (urllib.error.URLError, OSError) as err:
                return {
                    "status": "uncertain",
                    "note": "Connessione fallita o esito sconosciuto. Verifica il gestionale prima di qualsiasi nuova richiesta.",
                    "error_type": type(err).__name__,
                }
            try:
                root = ET.fromstring(data)
                code = root.findtext(".//returnCode")
                doc_id = root.findtext(".//docId")
                doc_number = root.findtext(".//docNumber")
                if code == "0" and doc_id:
                    conn.execute("UPDATE submissions SET status='saved',doc_id=?,doc_number=? WHERE request_id=?",
                                 (doc_id,doc_number,request_id))
                    return {
                        "status": "saved_in_fattura24_not_sent_to_sdi",
                        "document_id": doc_id,
                        "document_number": doc_number,
                        "note": "Aprire Fattura24 e verificare ogni campo prima di inviare allo SdI.",
                    }
                return {
                    "status": "uncertain",
                    "note": "Risposta non di successo o incompleta. Verifica manualmente in Fattura24 prima di riprovare.",
                    "provider_code": code,
                }
            except ET.ParseError:
                return {"status": "uncertain", "note": "Risposta non riconosciuta; verifica manualmente in Fattura24."}
        finally:
            conn.close()
