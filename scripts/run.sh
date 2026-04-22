#!/bin/bash

set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PY="$BASE_DIR/edge_venv/bin/python"
APP_DIR="$BASE_DIR/backend"
PORT=8001

echo "👉 Starting backend on port $PORT"

# -----------------------------
# Check if port is in use
# -----------------------------
if lsof -i :$PORT >/dev/null; then
    echo "⚠️ Port $PORT is in use. Checking if it's uvicorn..."

    PID=$(lsof -t -i :$PORT)

    if ps -p $PID -o cmd= | grep -q "uvicorn"; then
        echo "🧹 Killing uvicorn process (PID $PID)..."
        kill -9 $PID
    else
        echo "❌ Port $PORT is used by another process (not uvicorn). Not killing it."
        exit 1
    fi
fi

# -----------------------------
# Run server
# -----------------------------
cd "$APP_DIR"

exec "$VENV_PY" -m uvicorn main:app \
    --reload \
    --host 0.0.0.0 \
    --port $PORT
