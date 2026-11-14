"""Prove write rejection without keys, opt-in, or any provider traffic."""
import urllib.request
import pytest
from core import Document
from fattura24_client import register_invoice, configured
from fattura24_extra import Customer, save_customer


def test_disabled_writes_never_access_network(monkeypatch):
    monkeypatch.delenv("FATTURA24_API_KEY", raising=False)
    monkeypatch.setenv("FATTURA24_ENABLE_WRITES", "false")
    def forbidden(*args, **kwargs):
        pytest.fail("Unexpected provider/network call")
    monkeypatch.setattr(urllib.request, "urlopen", forbidden)
    assert configured() is False
    doc = Document(customer_name="DEMO", rows=[dict(description="Demo", quantity="2", price_net="10", vat_code="22")])
    with pytest.raises(RuntimeError, match="Scrittura disabilitata"):
        register_invoice(doc, "demo-no-write", "NOT AUTHORIZED")
    customer = Customer(name="DEMO", address="Via Demo", postcode="00000", city="Demo", vat_code="00000000000")
    with pytest.raises(RuntimeError, match="Scrittura disabilitata"):
        save_customer(customer, "demo-no-customer-write", "NOT AUTHORIZED")
