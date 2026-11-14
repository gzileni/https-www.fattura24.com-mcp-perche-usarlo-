---
name: fattura24
description: "Quando l'utente desidera interpretare i report Fattura24, controllare documenti con MCP autorizzato o preparare bozze di fatture/DDT senza inviarle."
---

# Fattura24 con Claude

## Modalità consentite

**Lettura:** utilizza un MCP Fattura24 realmente collegato e autenticato (se il client Claude lo supporta) e soltanto gli strumenti che espone. Non inventare connessioni o dati.

**Bozza:** se è collegato un server MCP di anteprima locale, usa `bridge_status`, `prepare_invoice`, `invoice_xml_preview` e `prepare_ddt_notes`. La bozza non diventa mai una fattura/DDT registrato; l'XML è solo dimostrativo.

## Procedura

1. Verifica quali tool sono realmente disponibili.
2. Se l'utente chiede fatture o DDT, chiedi solo i campi indispensabili mancanti; non inventare dati fiscali o aliquote.
3. Mostra ragione sociale, righe, quantità, prezzi, IVA e totali con le ipotesi.
4. Contrassegna chiaramente ogni risultato come `ANTEPRIMA NON REGISTRATA`.
5. Per l'emissione e lo SdI usa l'interfaccia ufficiale, finché non esiste un connettore di scrittura autorizzato, testato e supportato.
6. Non chiedere chiavi API o token in chat.
7. Nessuna skill può installare o avviare Docker sul PC dall'esecuzione cloud. Suggerisci gli script locali solo se l'utente controlla il dispositivo.
8. Non accedere a server privati senza consenso, non esporre token nei log e non aprire porte pubbliche.

## Documentazione

https://www.fattura24.com/mcp/perche-usarlo/
https://www.fattura24.com/documentazione-legale/regolamento-api/
