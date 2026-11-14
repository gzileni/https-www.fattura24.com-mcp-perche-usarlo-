#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if ! command -v docker >/dev/null 2>&1; then
  echo "Docker Desktop non installato. Installalo manualmente: https://docs.docker.com/desktop/setup/install/mac-install/" >&2
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  if [ -d /Applications/Docker.app ]; then
    echo "Provo ad aprire Docker Desktop ..."
    open -a Docker
    for i in $(seq 1 40); do
      if docker info >/dev/null 2>&1; then break; fi
      sleep 2
    done
  fi
fi
docker info >/dev/null 2>&1 || { echo "Docker Engine non disponibile" >&2; exit 2; }
if [ ! -e .env ]; then
  umask 077
  printf 'BRIDGE_TOKEN=%s\n' "$(openssl rand -hex 32)" > .env
  echo "Creato .env privato. Non pubblicarlo su GitHub."
fi
docker compose up -d --build
echo "Verifica il bridge: http://127.0.0.1:8765/health"
