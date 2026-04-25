#!/bin/bash

set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PY="$BASE_DIR/edge_venv/bin/python"
APP_DIR="$BASE_DIR/backend"
PORT=8001

echo "👉 Starting backend on port $PORT"

# -----------------------------
# HARD CLEAN (IMPORTANT FIX)
# -----------------------------
echo "🧹 Killing anything using port $PORT..."

# kill all processes on port
PIDS=$(lsof -t -i :$PORT || true)

if [ ! -z "$PIDS" ]; then
    echo "Found PIDs: $PIDS"
    kill -9 $PIDS || true
fi

# also kill uvicorn explicitly (extra safety)
pkill -f uvicorn || true

sleep 1

# -----------------------------
# Run server (NO reload = stable)
# -----------------------------
cd "$APP_DIR"

exec "$VENV_PY" -m uvicorn main:app \
    --host 0.0.0.0 \
    --port $PORT