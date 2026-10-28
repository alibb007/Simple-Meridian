#!/usr/bin/env bash
# Start Simple Meridian on macOS or Linux. Needs Docker Desktop (or Docker Engine).
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed. Get Docker Desktop: https://www.docker.com/products/docker-desktop/"
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "Docker is installed but not running. Start Docker Desktop, wait for it to finish starting, then run this again."
  exit 1
fi

echo "Building and starting Simple Meridian (the first build takes a few minutes)..."
docker compose up --build -d
echo "Waiting for the app to be ready..."
for _ in $(seq 1 60); do
  if curl -fs http://localhost:8501/_stcore/health >/dev/null 2>&1; then
    echo "Ready: http://localhost:8501"
    (command -v open >/dev/null && open http://localhost:8501) || (command -v xdg-open >/dev/null && xdg-open http://localhost:8501) || true
    echo "Stop it later with:  docker compose down"
    exit 0
  fi
  sleep 2
done
echo "The app did not answer yet. Check the logs with:  docker compose logs -f"
