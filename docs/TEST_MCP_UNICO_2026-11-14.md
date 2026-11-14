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

Il workflow pubblicazione è configurato per ripetere il collaudo dimostrativo
OAuth/wrapper dentro l’immagine candidata e nel digest GHCR pubblicato, entrambi
con `--network none`. Il risultato della nuova esecuzione verrà registrato dopo
il completamento del workflow; i risultati precedenti non vengono attribuiti
alla nuova immagine.

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
