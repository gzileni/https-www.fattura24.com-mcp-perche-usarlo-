---
name: fattura24
description: "Avvio automatico locale di Docker Fattura24 MCP e lavoro con gli strumenti del gestionale, quando Claude Code dispone di shell locale autorizzata."
---

# Fattura24 MCP — skill Claude Code

## Avvio senza clone: comportamento predefinito

Quando l'utente chiede di avviare Fattura24, scaricare l'immagine Docker, installare il bridge, testarlo o collegarlo a Claude:

1. Verifica che la sessione sia **Claude Code sul computer dell'utente**, con un tool shell disponibile. Una skill NON installa strumenti né dà automaticamente permessi di sistema. Su Claude Web o app mobile, spiega che non puoi controllare Docker Desktop remoto.
2. Prima di eseguire comandi che scaricano codice e avviano container richiedi l'approvazione del sistema e dell'utente; non aggirare le richieste di autorizzazione. Controlla Docker con `docker info`; se non è installato, comunica che va installato dall'utente.
3. **Non chiedere git clone, non richiedere Docker Compose né Python.** Usa lo script standalone della piattaforma dal repository pubblico:
   - Windows: `https://raw.githubusercontent.com/gzileni/https-www.fattura24.com-mcp-perche-usarlo-/main/scripts/launch-standalone.ps1`
   - macOS (Intel o Apple Silicon): `https://raw.githubusercontent.com/gzileni/https-www.fattura24.com-mcp-perche-usarlo-/main/scripts/launch-standalone.sh`
4. Scarica il launcher come file temporaneo, mostra il codice all'utente per la revisione e **solo dopo approvazione** eseguilo. Non eseguire pipe cieche `curl | bash` o `iex (irm ...)`. Usa `powershell -ExecutionPolicy Bypass -File <file>` su Windows oppure `bash <file>` su Mac.
5. Il launcher usa `docker pull ghcr.io/gzileni/fattura24-mcp-bridge:latest` e `docker run`, crea un token locale persistente, lascia le scritture disabilitate e pubblica la porta soltanto su `127.0.0.1:8765`.
6. Se `fattura24-mcp` esiste già e gira, lo lascia invariato. Se è fermo, lo riavvia senza distruggere dati o ruotare il token. **Non** sostituire automaticamente un container esistente. Il parametro `-ReplaceExisting` (Windows) o `--replace-existing` (Mac) richiede una seconda conferma esplicita.
7. Verifica `http://127.0.0.1:8765/health` e, se necessario, `docker logs --tail 50 fattura24-mcp`.
8. Se richiesto e se il tuo client lo supporta, proponi una connessione MCP Streamable HTTP locale a `http://127.0.0.1:8765/mcp` con `Authorization: Bearer <token>`, senza esporre il token in chat, screenshot o log. Il token locale è in `%LOCALAPPDATA%\Fattura24MCP\bridge.env` su Windows, `~/.config/fattura24-mcp/bridge.env` su macOS.
9. Per i test chiama soltanto `bridge_status` e `prepare_invoice` con dati inventati. **Mai** creare fatture o aggiornare clienti soltanto per verificare il collegamento.

## Uso strumenti Fattura24

Usa soltanto MCP effettivamente collegati e autorizzati. MCP ufficiale Fattura24 serve alla consultazione dei dati. Il bridge locale offre anteprime, salvataggio opzionale di alcune fatture semplici e operazioni clienti. Prima di ogni salvataggio: riepilogo, conferma umana esplicita e richiesta univoca. Non dichiarare che i DDT vengono registrati o che la fattura viene inviata allo SdI: non è implementato.

Fonti:
- https://www.fattura24.com/mcp/perche-usarlo/
- https://github.com/gzileni/https-www.fattura24.com-mcp-perche-usarlo-/tree/main/scripts
