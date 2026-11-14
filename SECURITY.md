# Sicurezza — Fattura24 MCP Bridge

**PROTOTIPO PER ANTEPRIME, NON PER FATTURAZIONE OPERATIVA.**

- Non inserire in GitHub, nei prompt o negli issue: token, chiavi API Fattura24, dati fiscali/cliente reali, XML reali.
- `.env` è escluso da Git e dalla build Docker. Gli script generano localmente un token casuale. Non inviare il file a nessuno.
- Il container si lega soltanto a `127.0.0.1:8765`. Non aprire la porta sul router, non esporre il servizio con un tunnel pubblico senza autenticazione end-to-end e TLS.
- Il token Bearer è un meccanismo locale minimo, **non** un sistema OAuth per un MCP pubblico e multiutente.
- Il processo nel container gira come utente non privilegiato, con filesystem in sola lettura e capability eliminate.
- Le bozze XML non sono conformità certificata FatturaPA/Fattura24. Nessuna scrittura nel gestionale è implementata.
- Un eventuale modulo SaveDocument deve essere progettato separatamente con consenso umano verificabile, controllo anti-duplicati, gestione degli errori incerti, registrazione non sensibile degli eventi e verifica contrattuale API.
- Le app ChatGPT cloud e Claude cloud non hanno capacità standard di installare/avviare Docker sul tuo PC.
- Per segnalare vulnerabilità: apri una segnalazione privata a chi mantiene il repository, senza pubblicare token o dati sensibili.
