from decimal import Decimal
import xml.etree.ElementTree as ET
from core import Document, compute, preview, make_xml
import pytest

def sample(**kw):
    return Document(customer_name="Cliente demo", rows=[{
        "description": "Merce demo", "quantity": "2", "price_net": "10",
        "vat_code": "22", "vat_description": "22%",
    }], **kw)

def test_totals():
    doc = sample()
    assert compute(doc) == [(Decimal("20.00"), Decimal("4.40"))]
    assert preview(doc)["total"] == "24.40"

def test_xml_escaped_and_is_only_preview():
    doc = Document(customer_name="Rossi & Figli <test>", rows=[{
        "description": "Olive & agrumi", "quantity": "3", "price_net": "2",
        "vat_code": "10", "vat_description": "10%",
    }])
    xml = make_xml(doc)
    assert "&amp;" in xml
    assert ET.fromstring(xml).findtext("./Customer") == "Rossi & Figli <test>"
    assert "ESEMPIO NON INVIABILE" in xml

def test_zero_rate_requires_nature():
    doc = Document(customer_name="Demo", rows=[{
        "description": "Demo", "quantity": "1", "price_net": "10",
        "vat_code": "0", "vat_description": "0%",
    }])
    with pytest.raises(ValueError):
        compute(doc)

def test_bad_rate_rejected():
    doc = Document(customer_name="Demo", rows=[{
        "description": "Demo", "quantity": "1", "price_net": "10",
        "vat_code": "9", "vat_description": "9%",
    }])
    with pytest.raises(ValueError):
        compute(doc)
