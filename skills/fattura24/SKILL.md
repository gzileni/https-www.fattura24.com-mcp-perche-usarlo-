---
name: fattura24
description: "Workflow portabile per consultare Fattura24 con MCP e preparare bozze di documenti senza registrarli."
---

# Workflow portabile Fattura24

- Usa soltanto i tool realmente disponibili. Non simulare connessioni.
- Server MCP ufficiale: lettura/report; bozza locale del bridge: anteprima.
- Il bridge dispone di SaveDocument facoltativo per fatture semplici (I, FE), disabilitato finché il proprietario non configura la propria chiave Fattura24 ed esplicitamente abilita le scritture. `invoice_api_payload_preview` mostra XML e importi.
- Lo strumento di registrazione `save_invoice_to_fattura24` va usato SOLO dopo conferma esplicita dell'utente sul documento completo, con richiesta univoca e frase di conferma. I DDT non sono registrabili tramite il bridge attuale.
- Non promettere creazione DDT, numerazione, invio email o invio SdI.
- Analizza importi con periodo, filtri, valuta e differenza fra incassato e fatturato.
- Prima di qualsiasi futura scrittura richiedi consenso esplicito e verifica dei dati.
- Proteggi chiavi e dati reali; nessun segreto nei prompt o nel repository.
- Il cloud non avvia Docker Desktop e non raggiunge localhost senza integrazioni aggiuntive.

- SaveCustomer aggiorna anche schede esistenti: anteprima e consenso distinto. GetFile recupera PDF già presenti; proteggerli come dati riservati. TestKey si usa una sola volta su richiesta.


## Server MCP unico (architettura corrente)

- Configurare soltanto `http://127.0.0.1:8765/mcp` nel client locale autorizzato.
- Dopo l’avvio, se l’utente chiede dati reali e lo stato ufficiale è scollegato,
  eseguire `docker exec -it fattura24-mcp python /app/connect_official.py` nella
  shell locale autorizzata e far completare all’utente il login nel browser.
  Non chiedere password, API key o token OAuth in chat. Il comando resta in
  attesa fino a completamento o scadenza; non dichiarare collegato l’account
  senza l’esito positivo. Non avviare OAuth nei test con dati dimostrativi.
- Aggiornare `tools/list` dopo OAuth: i tool ufficiali mantengono nomi e schemi
  scoperti dal provider; il bridge inoltra chiamate e risposte senza replicarli.
- Implementare tool locali soltanto per i gap, con nomi non in conflitto.
- I tool ufficiali non sono un secondo MCP da configurare: il container è il
  client OAuth del servizio remoto e li espone insieme ai tool locali.
- L’istanza è personale per un solo account; il token locale autorizza anche
  la consultazione dell’account collegato. Nessuna scrittura per i test.
