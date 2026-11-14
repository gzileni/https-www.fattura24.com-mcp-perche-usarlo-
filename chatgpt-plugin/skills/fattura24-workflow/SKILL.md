---
name: fattura24-workflow
description: "Consultazione Fattura24 e deploy sicuro del bridge Docker quando un esecutore locale autorizzato è effettivamente disponibile."
---

# Fattura24 — istruzioni per plugin ChatGPT

1. Per consultazioni e report usa soltanto gli strumenti reali del MCP ufficiale Fattura24 con OAuth dell'utente. Non inventare dati o tool.
2. Su richiesta «avvia Docker», «scarica immagine», «testa plugin», **controlla la presenza effettiva di un esecutore di comandi sul dispositivo locale dell'utente**. Un plugin ChatGPT cloud standard NON ha accesso automatico a PowerShell, Terminale o Docker Desktop. Una skill non crea tale accesso.
3. Se è disponibile **un esecutore locale collegato e autorizzato**, rispetta i permessi di esecuzione e le autorizzazioni già fornite per scaricare/eseguire il launcher. Non bypassare permessi di sistema. Nessun clone del repository o Compose necessario.
4. Launcher da verificare e approvare prima dell'esecuzione:
   - Windows: https://raw.githubusercontent.com/gzileni/https-www.fattura24.com-mcp-perche-usarlo-/main/scripts/launch-standalone.ps1
   - macOS: https://raw.githubusercontent.com/gzileni/https-www.fattura24.com-mcp-perche-usarlo-/main/scripts/launch-standalone.sh
5. Lo script scarica `ghcr.io/gzileni/fattura24-mcp-bridge:latest`, avvia il container locale `fattura24-mcp`, genera un token privato e non abilita le scritture. Se il container è già attivo non lo sostituisce. Non applicare parametri di sostituzione senza autorizzazione separata.
6. Se NON è disponibile un esecutore locale, dichiara il limite chiaramente e indica lo script da eseguire manualmente; non affermare di aver avviato Docker. Il plugin attuale punta al MCP ufficiale Fattura24, non al bridge sulla macchina dell'utente.
7. L'endpoint MCP locale `http://127.0.0.1:8765/mcp` richiede Bearer token. **ChatGPT cloud non può collegarsi a 127.0.0.1 del PC** senza infrastruttura di connessione sicura, supportata e autenticata. Non rendere pubblica direttamente la porta Docker.
8. Non creare fatture o clienti reali per test; usare `bridge_status` e anteprime con dati di fantasia. DDT e invio SdI non sono implementati.

9. Il launcher esegue il collaudo incluso nell’immagine. Ripetere con `docker exec fattura24-mcp python /app/smoke_test.py`: non serve Python sul computer. Riportare separatamente esito Docker/MCP locale, connessione del client e OAuth ufficiale. Un test nel runner GitHub Linux non verifica il PC Windows dell’utente.


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
