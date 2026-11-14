#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if ! command -v docker >/dev/null 2>&1; then
    echo "Docker Desktop non installato: https://docs.docker.com/desktop/setup/install/mac-install/" >&2
    exit 1
fi
if ! docker info >/dev/null 2>&1; then
    if [ -d /Applications/Docker.app ]; then
        echo "Provo ad avviare Docker Desktop..."
        open -a Docker
        for i in $(seq 1 40); do
            docker info >/dev/null 2>&1 && break
            sleep 2
        done
    fi
fi
docker info >/dev/null 2>&1 || { echo "Docker Engine non disponibile" >&2; exit 2; }
if [ ! -e .env ]; then
    umask 077
    printf 'BRIDGE_TOKEN=%s\nFATTURA24_ENABLE_WRITES=false\n' "$(openssl rand -hex 32)" > .env
    echo "Creato .env privato con scritture disabilitate."
fi
echo "Scarico immagine da GitHub Container Registry..."
docker compose pull
docker compose up -d --no-build
echo "Verifica http://127.0.0.1:8765/health"
