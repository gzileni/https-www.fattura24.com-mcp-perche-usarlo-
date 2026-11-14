#!/usr/bin/env python3
"""Interactive OAuth setup inside the container. Never print/store user secrets.

Run: docker exec -it fattura24-mcp python /app/connect_official.py
Open the displayed official authorization URL in the browser on the Docker host.
All tools, including the official wrappers, stay at http://127.0.0.1:8765/mcp.
"""
import json
import os
import sys
import time
import urllib.request


def request(method, path):
    token = os.environ.get("BRIDGE_TOKEN")
    if not token:
        raise RuntimeError("BRIDGE_TOKEN non configurato nel container")
    req = urllib.request.Request("http://127.0.0.1:8765" + path, method=method,
        data=b"" if method == "POST" else None, headers={"Authorization": "Bearer " + token})
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.load(response)


def main():
    result = request("POST", "/official/connect")
    shown = None
    for _ in range(150):
        if result.get("state") == "ready":
            print("[OK] Fattura24 collegato. Tool ufficiali:")
            print(", ".join(result["tool_names"]))
            print("Aggiorna tools/list o riconnetti il client allo stesso /mcp.")
            return
        if result.get("authorization_url") and result["authorization_url"] != shown:
            shown = result["authorization_url"]
            print("Apri nel browser del computer su cui gira Docker:")
            print(shown, flush=True)
        if result.get("state") == "authorization_or_connection_required":
            raise RuntimeError("OAuth non completato o servizio non raggiungibile. Ripetere il collegamento dal client locale.")
        time.sleep(2)
        result = request("GET", "/official/status")
    raise RuntimeError("Autorizzazione scaduta; nessun dato gestionale modificato")


if __name__ == "__main__":
    try:
        main()
    except (Exception, KeyboardInterrupt):
        print("[ERRORE] Collegamento OAuth non completato. Verificare connettivita e ripetere il comando.", file=sys.stderr)
        sys.exit(1)
