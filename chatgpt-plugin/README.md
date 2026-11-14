# Plugin ChatGPT (configurazione portabile)

Questa cartella contiene un **plugin separato** utilizzabile come sorgente per un'installazione privata che accede al **MCP ufficiale Fattura24** via OAuth.

- `plugin.json`: metadati del plugin.
- `mcp.json`: URL ufficiale MCP; OAuth, nessuna chiave segreta nel codice.
- `skills/fattura24-workflow/SKILL.md`: comportamento prudente.

**Non** include un server MCP locale, perché `localhost` non è raggiungibile dal cloud ChatGPT. Per integrare un bridge personale, occorre prima un endpoint HTTPS autenticato e un controllo della sicurezza; non mettere un URL segnaposto in una configurazione dichiarata funzionante.

Il plugin privato Fattura24 AI Assistant precedentemente creato in ChatGPT è un oggetto **distinto**; caricare questi file su GitHub non lo aggiorna automaticamente.

Per un uso diretto, apri ChatGPT → Plugin e collega un connettore disponibile compatibile con Fattura24. Dopo aver autorizzato OAuth, chiedi una lettura di prova (es. report fatturato). Nessuna chiave API OpenAI richiesta per questo repository.

Fonti: https://www.fattura24.com/mcp/riferimento-tecnico/ e https://www.fattura24.com/mcp/toolDisponibili/
