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

## Evidenze GitHub

Commit di implementazione: `05483643874f8595f410e630ac6af5640d1375be`.

- [Tests](https://github.com/gzileni/https-www.fattura24.com-mcp-perche-usarlo-/actions/runs/43604815687): **SUPERATO**, inclusi 10 test Python e integrazione MCP nel container.
- [Pubblicazione GHCR](https://github.com/gzileni/https-www.fattura24.com-mcp-perche-usarlo-/actions/runs/43604815714): **SUPERATO**: candidato e digest pubblicato, entrambi con rete disabilitata, inclusi tool di collegamento dalla chat, URL elicitation/link, OAuth PKCE simulato e wrapper del bilancino. Superati anche pip check e launcher Linux con riuso del container.


Immagine pubblicata: `ghcr.io/gzileni/fattura24-mcp-bridge:latest`, tag
`sha-0548364`, digest indice:
`sha256:61453061f55a6c07ce88f082d5c4a7f384797ec8544cd326a1ca8448844254ff`.
Build AMD64/ARM64; esecuzione dei test su AMD64 Linux. I log confermano:
`[OK] Chat OAuth tool + native URL request/link fallback + PKCE + report_bilancino on SAME /mcp; no real network`.
