---
name: fattura24-workflow
description: "Consultazione Fattura24 e deploy sicuro del bridge Docker quando un esecutore locale autorizzato è effettivamente disponibile."
---

# Fattura24 — istruzioni per plugin ChatGPT

1. Per consultazioni e report usa soltanto gli strumenti reali del MCP ufficiale Fattura24 con OAuth dell'utente. Non inventare dati o tool.
2. Su richiesta «avvia Docker», «scarica immagine», «testa plugin», **controlla la presenza effettiva di un esecutore di comandi sul dispositivo locale dell'utente**. Un plugin ChatGPT cloud standard NON ha accesso automatico a PowerShell, Terminale o Docker Desktop. Una skill non crea tale accesso.
3. Se è disponibile **un esecutore locale collegato e autorizzato**, richiedi la normale conferma per scaricare/eseguire il launcher. Non bypassare permessi di sistema. Nessun clone del repository o Compose necessario.
4. Launcher da verificare e approvare prima dell'esecuzione:
   - Windows: https://raw.githubusercontent.com/gzileni/https-www.fattura24.com-mcp-perche-usarlo-/main/scripts/launch-standalone.ps1
   - macOS: https://raw.githubusercontent.com/gzileni/https-www.fattura24.com-mcp-perche-usarlo-/main/scripts/launch-standalone.sh
5. Lo script scarica `ghcr.io/gzileni/fattura24-mcp-bridge:latest`, avvia il container locale `fattura24-mcp`, genera un token privato e non abilita le scritture. Se il container è già attivo non lo sostituisce. Non applicare parametri di sostituzione senza autorizzazione separata.
6. Se NON è disponibile un esecutore locale, dichiara il limite chiaramente e indica lo script da eseguire manualmente; non affermare di aver avviato Docker. Il plugin attuale punta al MCP ufficiale Fattura24, non al bridge sulla macchina dell'utente.
7. L'endpoint MCP locale `http://127.0.0.1:8765/mcp` richiede Bearer token. **ChatGPT cloud non può collegarsi a 127.0.0.1 del PC** senza infrastruttura di connessione sicura, supportata e autenticata. Non rendere pubblica direttamente la porta Docker.
8. Non creare fatture o clienti reali per test; usare `bridge_status` e anteprime con dati di fantasia. DDT e invio SdI non sono implementati.
