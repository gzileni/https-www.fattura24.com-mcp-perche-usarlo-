"""Offline tests for safe API payload creation. Never call Fattura24 in CI."""
import xml.etree.ElementTree as ET
from fattura24_extra import Customer, customer_xml
from core import Document, fattura24_xml

def test_customer_xml():
    customer = Customer(name="Rossi & Figli", address="Via Roma 1", postcode="00100",
                        city="Roma", vat_code="01234567890")
    root = ET.fromstring(customer_xml(customer))
    assert root.findtext("./Document/CustomerName") == "Rossi & Figli"
    assert root.findtext("./Document/CustomerVatCode") == "01234567890"

def test_real_invoice_xml_is_save_document_not_fatturapa():
    doc = Document(customer_name="Cliente demo", customer_address="Via Roma 1",
                   customer_postcode="00100", customer_city="Roma",
                   customer_vat_code="01234567890", destination_code="0000000",
                   rows=[{"description":"Prodotto","quantity":"2",
                          "price_net":"10","vat_code":"22","vat_description":"22%"}])
    root = ET.fromstring(fattura24_xml(doc))
    assert root.tag == "Fattura24"
    assert root.findtext("./Document/Total") == "24.40"
