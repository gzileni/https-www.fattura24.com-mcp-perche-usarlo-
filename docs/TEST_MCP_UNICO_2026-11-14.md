# Collaudo del server MCP unico — 14 novembre 2026

Architettura verificata: un solo server/endpoint `/mcp`; tool ufficiali esposti
come wrapper e tool locali aggiuntivi per i gap. È una nuova implementazione
rispetto al report E2E precedente, che riguardava il solo bridge di anteprime.

## Test eseguiti nell’ambiente Linux di lavoro

- **10 test pytest superati**, incluse le regressioni locali e il nuovo test
  integrato OAuth + federazione.
- Handshake e tool locali del server Uvicorn: **superati**, token assente/errato
  rifiutati, sei anteprime dimostrative e gestione degli input errati.
- Provider ufficiale simulato via `httpx.MockTransport`: **superato** il flusso
  DCR/PKCE S256 con controllo state e callback; persistenza privata con `0600`.
- Nuova connessione dopo riavvio simulato: **superati** ripristino credenziali
  e rinnovo del token scaduto. È stato corretto il ripristino della scadenza
  assoluta e dell’endpoint token, che il solo caricamento SDK non conservava.
- **Un unico `tools/list`** espone `prepare_invoice` locale e `report_bilancino`
  dal provider simulato. Schema identico a quello scoperto; nomi non modificati.
- **Un unico `tools/call`** inoltra `report_bilancino` con argomenti invariati
  e restituisce contenuto, structuredContent e isError originali.
- Errori del provider preservati; input contrario allo schema rifiutato prima
  di chiamare il tool remoto. Ticket non read-only escluso e non invocato.
- Istanza scollegata: **nessun contatto al provider**, nessuno schema ufficiale
  fittizio, chiamata ufficiale rifiutata con richiesta di collegamento.

Dati demo del bilancino: ricavi 1.000, costi 600, EBITDA 400, etichetta `demo`.
Sono valori del provider simulato, non valori dell’account utente.

## Docker/GitHub Actions

Commit implementato: `acde8055291b312e31a7354c3fa50cf0997b0589`.

[Workflow Tests](https://github.com/gzileni/https-www.fattura24.com-mcp-perche-usarlo-/actions/runs/43598911481): **SUPERATO** (Python, build Docker e MCP integration).

[Workflow GHCR](https://github.com/gzileni/https-www.fattura24.com-mcp-perche-usarlo-/actions/runs/43598911442): **SUPERATO**, inclusi candidato, pubblicazione multiarchitettura, pull per digest, collaudo del pubblicato e launcher Linux eseguito due volte con stesso container.

Il collaudo dimostrativo OAuth/wrapper è stato **realmente eseguito** dentro
l’immagine candidata e nel digest GHCR pubblicato, entrambi con `--network none`:
`[OK] OAuth PKCE demo + report_bilancino wrapper + local tools on the SAME /mcp; no real network`.
Anche lo smoke test dei sei tool locali e `pip check` sono superati.

| Identità/verifica | Esito |
| --- | --- |
| Tag immagine | `latest`, `sha-acde805` |
| Digest indice pubblico | `sha256:bb294863dc6d528fa69bc94b6fe880c2a08d7e44ef8838231e36c09cb0a0eb0b` |
| Manifest AMD64 eseguito | `sha256:47997010b204f05f5f2becd06d08df66a4d049fcb05585e93621f409ebd50b16` |
| Manifest ARM64 pubblicato | `sha256:bfb44ce8775756982ab04602d3980ede104bf32ab9765523c8c50c7dfc2c2912` |
| Accesso pubblico GHCR | Verificato anche senza login, digest `latest` coerente |
| Launcher Linux | Primo avvio e riuso superati, ID container invariato |
| Utente runtime | `bridge`, non root |
| HEALTHCHECK Docker | Al rapido inspect ancora `starting`; non attesa la transizione a `healthy`. Endpoint `/health` verificato direttamente |

L’esecuzione runtime del collaudo è AMD64; la build/manifest ARM64 non equivale a
un test completo su Apple Silicon o altro host ARM64. Nessuna verifica sul PC
Windows dell’utente. Il parser PowerShell CI ha verificato soltanto la sintassi
del launcher Windows.

## Verifiche pubbliche sul servizio reale (senza account)

Dall’ambiente Linux di lavoro sono state realmente interrogate soltanto le
informazioni pubbliche del provider e una richiesta initialize senza credenziali:

- `/.well-known/oauth-protected-resource`: HTTP **200**, resource
  `https://www.app.fattura24.com/mcp`.
- `/.well-known/oauth-authorization-server`: HTTP **200**; issuer, authorize,
  token e registration endpoint coerenti con il codice; PKCE **S256** dichiarato.
- `POST /mcp` initialize senza Authorization: HTTP **401**, challenge Bearer con
  URL dei metadata protetti. Nessuna registrazione client reale, nessun consenso,
  nessun token richiesto e nessun report interrogato in queste verifiche.

## Limiti

Nessun account Fattura24 reale è stato autenticato. Non sono verificati il consenso
OAuth reale, l’accettazione della callback loopback da parte del provider e il
bilancino reale. Non sono disponibili Docker Desktop Windows o una sessione
Claude Code dell’utente. Il plugin ChatGPT installato non è stato sostituito:
il suo collegamento al server unico richiede un client/esecutore autorizzato.

Nessuna API key reale usata; nessuna fattura creata, nessun cliente modificato,
nessuna scrittura abilitata. Per attivare le letture ufficiali sul proprio PC:

```sh
docker exec -it fattura24-mcp python /app/connect_official.py
```

Dopo login riuscito, aggiornare `tools/list` sullo stesso `/mcp`.
