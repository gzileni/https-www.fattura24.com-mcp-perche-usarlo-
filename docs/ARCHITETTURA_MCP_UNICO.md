# Un server MCP, wrapper ufficiali ed estensioni locali

Il client AI si collega a un unico endpoint Streamable HTTP:
`http://127.0.0.1:8765/mcp`, protetto da `BRIDGE_TOKEN`. Il container integra:

1. Il server MCP rivolto al client.
2. Un client MCP/OAuth verso `https://www.app.fattura24.com/mcp`.
3. Le implementazioni locali dei tool che coprono i gap del servizio ufficiale.

Il servizio ufficiale rimane gestito da Fattura24: la sua implementazione non è
copiata nel container. Il container espone wrapper, come richiesto, senza
replicare i report o inventare schemi dei tool.

## Discovery e dispatch

`tools/list` restituisce i tool locali e quelli realmente scoperti da Fattura24
quando l’account è collegato. Il wrapper conserva nome, inputSchema,
outputSchema, descrizioni e annotazioni. Sono ammessi solo i tool di lettura
documentati e con annotazioni `readOnlyHint=true`, `destructiveHint=false`.
`segnala_limite_connettore`, che invia un ticket esterno, è escluso.

Una chiamata con nome ufficiale viene inoltrata con i medesimi argomenti a
Fattura24; `CallToolResult`, contenuti, structuredContent e isError ritornano al
client. Il bridge non ricalcola il bilancino o altri report ufficiali.

I tool locali mantengono nomi distinti (`prepare_invoice`, anteprime XML,
appunti DDT ecc.). Un conflitto con i nomi ufficiali viene segnalato, senza
sovrascritture silenziose. La sola disponibilità di un tool non implica che
una scrittura sia attivata: SaveDocument/SaveCustomer restano opt-in, e sono
rimasti disabilitati durante tutti i test.

Senza OAuth, l’elenco contiene solo i tool locali: non vengono esposti wrapper
fittizi e non viene avviato automaticamente un login durante la discovery.
Il tool locale `connect_fattura24` è sempre esposto per avviare OAuth dalla chat.
`bridge_status.official` distingue credenziali presenti, stato e tool scoperti.
Non è una certificazione della validità corrente dei token: la validità reale
viene verificata dal provider durante il collegamento.

## Avvio e OAuth senza clone sul PC

Eseguire il launcher standalone della piattaforma con un esecutore locale
abilitato. Se il container esistente usa l’immagine precedente, aggiornarlo
esplicitamente con `-ReplaceExisting` (Windows) o `--replace-existing`
(macOS/Linux): il launcher ricrea il container conservando il volume e il token
privato. Il solo `docker pull` non aggiorna un container già creato.
Dopo la creazione del container con la nuova immagine, la procedura normale
parte dalla conversazione del client collegato al bridge:

1. Utente: «Collega Fattura24 e mostrami il bilancino 2026».
2. Assistente: chiama il tool locale `connect_fattura24`, disponibile anche
   prima del collegamento dell’account ufficiale.
3. Se il client annuncia capability `elicitation.url`, il server restituisce
   la richiesta standard URL-required (`-32042`), che il client può presentare
   come richiesta di apertura browser. Altrimenti il risultato contiene
   `authorization_url`, da mostrare come link cliccabile nella stessa chat.
4. L’utente effettua login e consenso esclusivamente sul sito Fattura24.
5. La callback raggiunge `http://127.0.0.1:8765/oauth/callback`. L’assistente
   richiama `connect_fattura24`; solo `state=ready` conferma discovery riuscita.
6. Aggiorna `tools/list` o riconnette il client e riprende la richiesta originale.

Non occorre eseguire PowerShell o `docker exec` per iniziare OAuth dalla chat.
`connect_official.py` rimane un’alternativa diagnostica facoltativa.
Il container non tenta di aprire un browser al proprio interno. La comparsa
concreta di una finestra/pulsante dipende dal supporto del client; resta disponibile
il normale link nella conversazione. Non è implementata una notifica push del
cambiamento dell’elenco.

La callback con questo URI deve essere accettata dal provider al momento della
registrazione OAuth. Questa accettazione e il login dell’account reale non sono
verificabili senza completare l’autorizzazione effettiva con Fattura24.

Il token del client MCP locale resta `BRIDGE_TOKEN`; non è un token Fattura24
e non viene mai inoltrato al provider. La configurazione del client resta
**una sola**: `/mcp`. `/official/connect`, `/official/status` e `/oauth/callback`
sono endpoint di configurazione OAuth, non server MCP aggiuntivi. Le prime
due route sono protette dal token locale; la callback verifica lo state.

## Persistenza e confini

- Istanza personale per **un solo account**: qualsiasi client con il token
  locale può consultare l’account Fattura24 collegato.
- OAuth con DCR, PKCE S256 e verifica dello state tramite SDK MCP; token e
  registrazione client restano in `/data/official-oauth.json`, file atomico
  con permessi `0600` nel volume Docker. Non è una cifratura del volume.
- Le scadenze assolute sono persistite; il rinnovo con refresh token viene
  provato anche dopo la creazione di una nuova connessione simulando un riavvio.
- Se il refresh non riesce o il consenso è revocato, non viene simulato un
  account collegato: occorre ripetere l’OAuth. Nessun retry di scritture.
- `BRIDGE_PUBLIC_URL` opzionale cambia l’origine della callback. Default:
  `http://127.0.0.1:8765`. Cambiarla invalida la registrazione OAuth memorizzata
  e richiede un nuovo collegamento. HTTP consentito solo su loopback.
- Uvicorn nell’immagine disabilita gli access log per evitare codici OAuth
  nei log della callback. Nessun token viene restituito dalle route di stato.
- Restano necessari il collegamento locale autorizzato e una soluzione di
  accesso adeguata se il client è nel cloud. Non esporre direttamente la porta
  locale su Internet. Il container non crea automaticamente un tunnel.

## Test

`tests/test_official_gateway.py` verifica OAuth PKCE, callback/state, persistenza,
refresh dopo riavvio, elenco unico di tool, dispatch di `report_bilancino`,
conservazione di schema/risultato/errori e blocco dei tool non read-only.
Il provider in questi test è interamente dimostrativo con `httpx.MockTransport`:
nessuna richiesta a un account Fattura24 e nessun dato reale.

Il workflow GHCR ripete questi test dimostrativi dentro l’immagine candidata e
quella pubblicata, con `--network none`, oltre al collaudo HTTP locale.

Fonti tecniche del provider:
- https://www.fattura24.com/mcp/riferimento-tecnico/
- https://www.fattura24.com/mcp/toolDisponibili/

Il trasporto mantiene le sessioni MCP (`Mcp-Session-Id`) per rispettare le capability dichiarate dal singolo client. L’URL e il formato Streamable HTTP restano invariati.
