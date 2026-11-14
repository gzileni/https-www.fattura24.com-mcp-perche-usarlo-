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
