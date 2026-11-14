---
name: fattura24
description: "Quando l'utente desidera interpretare i report Fattura24, controllare documenti con MCP autorizzato o preparare bozze di fatture/DDT senza inviarle."
---

# Fattura24 con Claude

## Modalità consentite

**Lettura:** utilizza un MCP Fattura24 realmente collegato e autenticato (se il client Claude lo supporta) e soltanto gli strumenti che espone. Non inventare connessioni o dati.

**Bozza:** se è collegato un server MCP di anteprima locale, usa `bridge_status`, `prepare_invoice`, `invoice_xml_preview` e `prepare_ddt_notes`. La bozza NON è registrata. Il bridge dispone anche di uno strumento opzionale di registrazione fatture semplici, diverso dall'XML dimostrativo.

## Procedura

1. Verifica quali tool sono realmente disponibili.
2. Se l'utente chiede fatture o DDT, chiedi solo i campi indispensabili mancanti; non inventare dati fiscali o aliquote.
3. Mostra ragione sociale, righe, quantità, prezzi, IVA e totali con le ipotesi.
4. Contrassegna chiaramente ogni risultato come `ANTEPRIMA NON REGISTRATA`.
5. Per registrare una fattura semplice, usa `invoice_api_payload_preview` per mostrare tutti i dati, poi solo dopo esplicita conferma umana usa `save_invoice_to_fattura24` con `request_id` unico e la frase `CONFERMO IL SALVATAGGIO IN FATTURA24`. Verifica che il bridge dica `writes_enabled=true`. Non usare per test casuali.
6. La registrazione non è invio SdI. Controlla il documento nell'interfaccia ufficiale, che resta necessaria per inviare allo SdI. Per DDT il bridge offre solo preparazione dati; NON dichiarare di aver creato un DDT in Fattura24.
7. Se la risposta API è incerta o va in timeout, NON ripetere la chiamata: controlla manualmente per evitare duplicati.
8. Non chiedere chiavi API o token in chat.
9. Nessuna skill può installare o avviare Docker sul PC dall'esecuzione cloud. Suggerisci gli script locali solo se l'utente controlla il dispositivo.
10. Non accedere a server privati senza consenso, non esporre token nei log e non aprire porte pubbliche.

## Documentazione

https://www.fattura24.com/mcp/perche-usarlo/
https://www.fattura24.com/documentazione-legale/regolamento-api/

11. Se effettivamente disponibili, `verify_fattura24_api_key` non è un health check periodico; `save_customer_to_fattura24` può aggiornare un cliente esistente e richiede specifica conferma; `download_document_pdf` recupera dati riservati in base64.
