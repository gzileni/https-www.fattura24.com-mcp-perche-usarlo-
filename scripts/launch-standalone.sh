#!/usr/bin/env bash
# macOS / Linux launcher: Docker only, no Git, Python or Compose.
set -euo pipefail
IMAGE='ghcr.io/gzileni/fattura24-mcp-bridge:latest'
NAME='fattura24-mcp'
REPLACE=''
if [[ $# -gt 0 ]]; then REPLACE="$1"; fi
if [[ "$REPLACE" != "" && "$REPLACE" != "--replace-existing" ]]; then
  echo "Usage: launch-standalone.sh [--replace-existing]" >&2; exit 2
fi
command -v docker >/dev/null || { echo 'Docker non installato.' >&2; exit 1; }
if ! docker info >/dev/null 2>&1; then
  if [[ "$(uname -s)" == "Darwin" && -d /Applications/Docker.app ]]; then
    open -a Docker
    for _ in {1..60}; do
      docker info >/dev/null 2>&1 && break
      sleep 2
    done
  fi
fi
docker info >/dev/null 2>&1 || { echo 'Docker Engine non disponibile.' >&2; exit 1; }
verify_bridge() {
  # Runs with the container's private token; no host Python or token disclosure.
  docker exec -e BRIDGE_URL=http://127.0.0.1:8765 "$NAME" python /app/smoke_test.py
}
if docker container inspect "$NAME" >/dev/null 2>&1; then
  if [[ "$REPLACE" != "--replace-existing" ]]; then
    if [[ "$(docker inspect -f '{{.State.Running}}' "$NAME")" == 'true' ]]; then
      echo 'Container gia attivo: nessuna modifica alle credenziali.'
    else
      docker start "$NAME" >/dev/null
      echo 'Container esistente riavviato.'
    fi
    verify_bridge
    exit 0
  fi
  echo 'Sostituzione esplicita del SOLO container; volume conservato.'
  docker rm -f "$NAME" >/dev/null
fi
STATE_DIR="$HOME/.config/fattura24-mcp"
ENV_FILE="$STATE_DIR/bridge.env"
umask 077
mkdir -p "$STATE_DIR"
if [[ ! -f "$ENV_FILE" ]]; then
  printf 'BRIDGE_TOKEN=%s\nFATTURA24_ENABLE_WRITES=false\n' "$(openssl rand -hex 32)" > "$ENV_FILE"
fi
chmod 600 "$ENV_FILE"
docker pull "$IMAGE"
docker volume create fattura24_state >/dev/null
docker run -d --name "$NAME" --restart unless-stopped \
  --env-file "$ENV_FILE" --read-only --tmpfs /tmp --cap-drop ALL \
  --security-opt no-new-privileges \
  -v fattura24_state:/data -p 127.0.0.1:8765:8765 \
  "$IMAGE" >/dev/null
for _ in {1..30}; do
  if [[ "$(curl -fsS --max-time 2 http://127.0.0.1:8765/health 2>/dev/null || true)" == 'ok' ]]; then
    verify_bridge
    echo '[OK] MCP locale http://127.0.0.1:8765/mcp'
    exit 0
  fi
  sleep 2
done
echo 'Container avviato ma health non risponde. docker logs fattura24-mcp' >&2
exit 1
