"""Pure preview calculations. No network calls and no document submission."""
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal
import xml.etree.ElementTree as ET
from pydantic import BaseModel, Field

SUPPORTED_RATES = {"0", "4", "5", "10", "22"}

class Row(BaseModel):
    description: str = Field(min_length=1, max_length=500)
    quantity: Decimal = Field(gt=0)
    price_net: Decimal = Field(ge=0)
    vat_code: str
    vat_description: str = ""
    vat_nature: str | None = None
    unit: str = ""

class Document(BaseModel):
    document_type: Literal["FE", "I"] = "FE"
    customer_name: str = Field(min_length=1)
    customer_address: str = ""
    customer_postcode: str = ""
    customer_city: str = ""
    customer_province: str = ""
    customer_country: str = "IT"
    customer_vat_code: str = ""
    customer_fiscal_code: str = ""
    destination_code: str = ""
    customer_pec: str = ""
    payment_code: str = ""
    object: str = ""
    rows: list[Row] = Field(min_length=1, max_length=100)

def compute(doc: Document):
    """Simplified example arithmetic, NOT complete Italian tax logic."""
    result = []
    for r in doc.rows:
        if r.vat_code not in SUPPORTED_RATES:
            raise ValueError("Aliquota non supportata in demo: serve verifica manuale")
        if r.vat_code == "0" and not r.vat_nature:
            raise ValueError("IVA 0%: natura operazione obbligatoria e da verificare")
        if r.vat_code != "0" and r.vat_nature:
            raise ValueError("Natura IVA prevista solo per 0%")
        net = (r.quantity * r.price_net).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        vat = (net * Decimal(r.vat_code) / 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        result.append((net, vat))
    return result

def preview(doc: Document) -> dict:
    items = compute(doc)
    net = sum((x for x, _ in items), Decimal("0"))
    vat = sum((y for _, y in items), Decimal("0"))
    return {
        "state": "preview_only",
        "customer": doc.customer_name,
        "document_type": doc.document_type,
        "net": f"{net:.2f}",
        "vat": f"{vat:.2f}",
        "total": f"{net + vat:.2f}",
        "warning": "Nessun documento salvato o inviato. Calcolo dimostrativo; verificare regime fiscale e arrotondamenti.",
    }

def make_xml(doc: Document) -> str:
    """Illustrative XML, NOT a validated Fattura24 or FatturaPA document."""
    result = preview(doc)
    root = ET.Element("DraftPreview")
    ET.SubElement(root, "Disclaimer").text = "ESEMPIO NON INVIABILE"
    ET.SubElement(root, "Customer").text = doc.customer_name
    for label in ("net", "vat", "total"):
        ET.SubElement(root, label.capitalize()).text = result[label]
    rows = ET.SubElement(root, "Rows")
    for row in doc.rows:
        entry = ET.SubElement(rows, "Row")
        for field in ("description", "quantity", "price_net", "vat_code"):
            ET.SubElement(entry, field).text = str(getattr(row, field))
    return ET.tostring(root, encoding="unicode")
