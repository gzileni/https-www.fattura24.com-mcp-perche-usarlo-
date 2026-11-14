# Autenticazione richiesta nella chat del plugin

È stato aggiunto `connect_fattura24`, esposto sullo stesso `/mcp` anche quando
l’account ufficiale non è collegato. La chat può avviare OAuth, richiedere
l’apertura del browser, verificare l’esito e riprendere il report richiesto.
PowerShell e `connect_official.py` non sono più il percorso normale di login.

## Verifiche eseguite

- 10 test pytest superati nell’ambiente Linux di lavoro.
- Richiesta `tools/list` prima del login: il tool di collegamento è presente;
  i report ufficiali non sono inventati o esposti senza discovery.
- Chiamata MCP `connect_fattura24`: flusso PKCE avviato con provider simulato,
  risposta con link OAuth e istruzione di richiedere l’autorizzazione in chat.
- Richiesta ripetuta: stesso flusso pendente e stesso URL, senza nuova registrazione.
- Client che dichiara `elicitation.url`: risposta JSON-RPC `-32042` con URL
  elicitation standard. Client senza capability: normale risultato con link.
- Callback valida dopo state verificato: nuovo richiamo del tool restituisce
  `ready`, senza nuovo login e senza riportare token; poi è disponibile
  `report_bilancino` nello stesso server insieme ai tool locali.
- Refresh token, persistenza, schema e risultato del report dimostrativo e
  blocco delle scritture restano coperti dal collaudo precedente.
- Sessioni MCP conservate tramite `Mcp-Session-Id`; smoke test aggiornato per
  propagare l’header e terminare la sessione alla fine del collaudo.

I test usano un provider simulato e non modificano dati su Fattura24.
La richiesta di apertura URL è verificata sul protocollo: non è stata osservata
la finestra effettiva in ChatGPT Desktop Windows, né completato un login reale.
Il normale link in chat resta il fallback per client senza tale supporto.

L’aggiornamento dell’immagine e il collegamento del client al container restano
prerequisiti. Un plugin che punta ancora direttamente al MCP remoto ufficiale
non vede automaticamente questo nuovo tool locale.

La successiva esecuzione GitHub Actions registra build e test del digest
pubblicato; le sue evidenze saranno aggiunte al termine.
