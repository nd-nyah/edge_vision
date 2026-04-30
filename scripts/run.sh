#!/bin/bash

set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$BASE_DIR/edge_venv"
VENV_PY="$VENV_DIR/bin/python"
APP_DIR="$BASE_DIR/backend"
REQ_FILE="$APP_DIR/requirements.txt"
PORT=8001

echo "🚀 Starting Edge Vision Backend..."

# -----------------------------
# 1. Create or update venv
# -----------------------------
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
else
    echo "♻️ Virtual environment exists — updating..."
fi

# Activate venv
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# -----------------------------
# 2. Install requirements
# -----------------------------
if [ -f "$REQ_FILE" ]; then
    echo "📦 Installing dependencies..."
    pip install -r "$REQ_FILE"
else
    echo "⚠️ requirements.txt not found in backend/"
fi

# -----------------------------
# 3. Kill existing process on port
# -----------------------------
if lsof -i :$PORT >/dev/null; then
    echo "⚠️ Port $PORT in use — stopping process..."

    PID=$(lsof -t -i :$PORT)

    if ps -p $PID -o cmd= | grep -q "uvicorn"; then
        echo "🧹 Killing uvicorn (PID $PID)..."
        kill -9 $PID
    else
        echo "❌ Port used by another process (not uvicorn)."
        exit 1
    fi
fi

# -----------------------------
# 4. Start backend
# -----------------------------
cd "$APP_DIR"

echo "🚀 Launching server on port $PORT..."

exec "$VENV_PY" -m uvicorn main:app \
    --reload \
    --host 0.0.0.0 \
    --port $PORT
