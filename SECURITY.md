# Sicurezza — Fattura24 MCP Bridge

**PROTOTIPO CON SCRITTURA OPZIONALE PER FATTURE SEMPLICI, NON CERTIFICATO PER FATTURAZIONE OPERATIVA.**

- Non inserire in GitHub, nei prompt o negli issue: token, chiavi API Fattura24, dati fiscali/cliente reali, XML reali.
- `.env` è escluso da Git e dalla build Docker. Gli script generano localmente un token casuale. Non inviare il file a nessuno.
- Il container si lega soltanto a `127.0.0.1:8765`. Non aprire la porta sul router, non esporre il servizio con un tunnel pubblico senza autenticazione end-to-end e TLS.
- Il token Bearer è un meccanismo locale minimo, **non** un sistema OAuth per un MCP pubblico e multiutente.
- Il processo nel container gira come utente non privilegiato, con filesystem in sola lettura e capability eliminate.
- `invoice_xml_preview` è un XML di esempio non inviabile. `invoice_api_payload_preview` produce il payload SaveDocument; i controlli fiscali restano manuali.
- Salvataggio reale disabilitato di default, attivabile solo con FATTURA24_API_KEY e FATTURA24_ENABLE_WRITES=true nel file .env locale.
- Il salvataggio fattura usa conferma testuale e `request_id` unico: un ID riutilizzato non ritenta automaticamente la scrittura. Timeout e risposte ambigue vanno verificati nel gestionale.
- SQLite anti-duplicati nel volume fattura24_state; non distruggere il volume durante una procedura di recupero.
- Un eventuale modulo SaveDocument deve essere progettato separatamente con consenso umano verificabile, controllo anti-duplicati, gestione degli errori incerti, registrazione non sensibile degli eventi e verifica contrattuale API.
- Le app ChatGPT cloud e Claude cloud non hanno capacità standard di installare/avviare Docker sul tuo PC.
- Per segnalare vulnerabilità: apri una segnalazione privata a chi mantiene il repository, senza pubblicare token o dati sensibili.
