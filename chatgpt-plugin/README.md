# Plugin ChatGPT (configurazione portabile)

Questa cartella contiene un **plugin separato** utilizzabile come sorgente per un'installazione privata che accede al **MCP ufficiale Fattura24** via OAuth.

- `plugin.json`: metadati del plugin.
- `mcp.json`: URL ufficiale MCP; OAuth, nessuna chiave segreta nel codice.
- `skills/fattura24-workflow/SKILL.md`: comportamento prudente.

**Non** include un server MCP locale, perché `localhost` non è raggiungibile dal cloud ChatGPT. Per integrare un bridge personale, occorre prima un endpoint HTTPS autenticato e un controllo della sicurezza; non mettere un URL segnaposto in una configurazione dichiarata funzionante.

Il plugin privato Fattura24 AI Assistant precedentemente creato in ChatGPT è un oggetto **distinto**; caricare questi file su GitHub non lo aggiorna automaticamente.

Per un uso diretto, apri ChatGPT → Plugin e collega un connettore disponibile compatibile con Fattura24. Dopo aver autorizzato OAuth, chiedi una lettura di prova (es. report fatturato). Nessuna chiave API OpenAI richiesta per questo repository.

Fonti: https://www.fattura24.com/mcp/riferimento-tecnico/ e https://www.fattura24.com/mcp/toolDisponibili/

## Distribuzione Docker tramite GitHub Packages

L'immagine Docker multipiattaforma viene pubblicata automaticamente con il workflow `.github/workflows/publish-ghcr.yml` in `ghcr.io/gzileni/fattura24-mcp-bridge:latest`. Gli script `scripts/start.ps1` e `scripts/start-mac.sh` la scaricano prima di avviare il container.

**Importante:** il plugin ChatGPT in questa cartella si collega esclusivamente al MCP ufficiale remoto Fattura24; non è autorizzato ad avviare Docker Desktop sul PC. L'avvio del container richiede un processo locale autorizzato. Per ChatGPT cloud la connessione a un MCP on-premises richiede Secure MCP Tunnel o un endpoint remoto con autenticazione adeguata. L'immagine GHCR pubblica non equivale a un server raggiungibile su Internet.
