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
- Se l’utente chiede il collegamento o dati reali mentre l’account è scollegato,
  chiamare `connect_fattura24` NELLA STESSA CHAT. Il client può presentare una
  richiesta nativa di apertura browser; in alternativa mostrare `authorization_url`
  come link cliccabile e chiedere all’utente di autorizzare sul sito Fattura24.
  Non richiedere comandi PowerShell o Docker per effettuare il login.
  Non chiedere password, API key o token OAuth in chat. Dopo il login richiamare
  `connect_fattura24` e dichiarare collegato solo con `state=ready`, quindi
  aggiornare tools/list e riprendere la richiesta originale. Non avviare OAuth
  nei test con dati dimostrativi. La configurazione locale del client e l’avvio
  del container restano prerequisiti distinti dal login dell’account.
- Aggiornare `tools/list` dopo OAuth: i tool ufficiali mantengono nomi e schemi
  scoperti dal provider; il bridge inoltra chiamate e risposte senza replicarli.
- Implementare tool locali soltanto per i gap, con nomi non in conflitto.
- I tool ufficiali non sono un secondo MCP da configurare: il container è il
  client OAuth del servizio remoto e li espone insieme ai tool locali.
- L’istanza è personale per un solo account; il token locale autorizza anche
  la consultazione dell’account collegato. Nessuna scrittura per i test.
