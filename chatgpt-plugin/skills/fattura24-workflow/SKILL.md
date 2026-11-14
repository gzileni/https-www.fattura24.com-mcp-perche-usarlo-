---
name: fattura24-workflow
description: "Usa questa skill quando l'utente chiede dati di fatturato, IVA, incassi, pagamenti o documenti dal proprio Fattura24, oppure vuole preparare una bozza senza registrarla."
---

# Fattura24 — lettura e bozze

1. Usa soltanto strumenti MCP **realmente disponibili** e autorizzati nel contesto. Se l'accesso OAuth non è presente, chiedi di completarlo nell'interfaccia ufficiale, senza raccogliere password o token in chat.
2. Leggi e confronta fatturato, documenti e report solo dal server MCP ufficiale. Per ogni risposta indica periodo, perimetro e differenza fra fatturato e incasso.
3. La configurazione di questo plugin include **solo il MCP ufficiale di Fattura24**: non esiste alcuna connessione implicita al server Docker del repository. Il bridge Docker può salvare fatture semplici solo se connesso separatamente con endpoint sicuro e attivazione delle scritture. Non inventare tool di scrittura dove non sono presenti.
4. Per la richiesta «crea fattura» o «crea DDT», puoi preparare **una bozza testuale** con dati e calcoli verificabili. Non affermare che il documento sia stato registrato, numerato, inviato via email o trasmesso allo SdI.
5. Prima di operazioni irreversibili in future integrazioni, mostra anteprima, imponibile, IVA, totale, cliente, righe e condizioni, e richiedi conferma esplicita.
6. Se l'utente vuole provare il bridge locale, rimanda a README del repository. Il cloud ChatGPT non può avviare autonomamente Docker Desktop né connettersi a 127.0.0.1 del PC.
7. Non attribuire alla documentazione del fornitore compatibilità che non è stata verificata. Valuta casi speciali IVA con il commercialista.
