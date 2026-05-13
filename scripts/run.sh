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

source "$VENV_DIR/bin/activate"

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
# 4. Detect FastAPI entrypoint (FIXED)
# -----------------------------
cd "$APP_DIR"

echo "🔍 Detecting FastAPI entrypoint..."

APP_FILE=$(find . -type f \( -name "main.py" -o -name "app.py" -o -name "server.py" \) | head -n 1)

if [ -z "$APP_FILE" ]; then
    echo "❌ No FastAPI entry file found (main.py/app.py/server.py)"
    echo "👉 Run: find backend -type f -name '*.py'"
    exit 1
fi

# Convert file path → module path
APP_MODULE=$(echo "$APP_FILE" \
    | sed 's|^\./||' \
    | sed 's|\.py$||' \
    | sed 's|/|.|g')

echo "✅ Found module: $APP_MODULE"

# -----------------------------
# 5. Start backend
# -----------------------------
echo "🚀 Launching server on port $PORT..."

exec "$VENV_PY" -m uvicorn "$APP_MODULE:app" \
    --reload \
    --host 0.0.0.0 \
    --port $PORT