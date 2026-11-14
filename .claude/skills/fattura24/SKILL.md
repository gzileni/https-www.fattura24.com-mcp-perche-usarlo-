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

## Installazione e avvio locale, solo in Claude Code con shell autorizzata

Se l'utente chiede «avvia Fattura24», «scarica l'immagine», «deploy locale»:
1. Verifica di operare sul **computer locale** (non su claude.ai, una VM remota o una chat senza terminale). Richiedi il normale consenso all'esecuzione dei comandi shell; non aggirare i prompt di autorizzazione.
2. Usa il repository clonato: su Windows esegui `powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1`; su Mac esegui `bash ./scripts/start-mac.sh`. I comandi verificano Docker, scaricano `ghcr.io/gzileni/fattura24-mcp-bridge:latest`, avviano il container e creano un token locale. Non installano Docker Desktop in modo occulto.
3. Testa `http://127.0.0.1:8765/health` e se il client è compatibile con MCP Streamable HTTP, configura l'endpoint locale `http://127.0.0.1:8765/mcp` e l'header Bearer con token dal file `.env`, solo dentro una configurazione locale privata. **Non stampare il token** in log, chat o output condivisi. Chiedi autorizzazione prima di modificare la configurazione del client.
4. Non chiamare mai `save_invoice_to_fattura24` o `save_customer_to_fattura24` per testare la connessione. Usa `bridge_status` e `prepare_invoice` con dati fittizi.
5. Se Docker non è installato, segnala chiaramente che la skill non può funzionare e fornisci il link al sito Docker. Se il PC è spento non esiste avvio da remoto.

Nota: l'installazione del repository e l'esecuzione locale sono prerequisiti. Una skill **non** concede capacità di esecuzione da sola; funziona solo in un host che consenta strumenti shell.
