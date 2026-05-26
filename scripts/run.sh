#!/bin/bash
set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

HOST_VENV="$BASE_DIR/host_venv"
PY="$HOST_VENV/bin/python"
HOST_CAM="$BASE_DIR/host_camera_service.py"
PID_FILE="$BASE_DIR/host_camera.pid"

echo "🚀 Setting up HOST CAMERA ENV..."

# =====================================================
# 0. STOP OLD CAMERA PROCESS (if running)
# =====================================================
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")

    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "🛑 Stopping old host camera (PID $OLD_PID)..."
        kill -9 $OLD_PID || true
    fi

    rm -f "$PID_FILE"
fi

# Kill anything using port 9000
if lsof -i :9000 >/dev/null 2>&1; then
    echo "⚠️ Port 9000 in use — killing process..."
    kill -9 $(lsof -t -i :9000) || true
fi

# =====================================================
# 1. DELETE OLD VENV
# =====================================================
if [ -d "$HOST_VENV" ]; then
    echo "🧹 Removing old host env..."
    rm -rf "$HOST_VENV"
fi

# =====================================================
# 2. CREATE VENV
# =====================================================
python3 -m venv "$HOST_VENV"

$PY -m pip install --upgrade pip

# =====================================================
# 3. SYSTEM DEPENDENCIES (JETSON IMPORTANT)
# =====================================================
echo "📦 Installing system OpenCV (Jetson optimized)..."

sudo apt update
sudo apt install -y python3-opencv

# =====================================================
# 4. PYTHON DEPENDENCIES (NO OPENCV HERE)
# =====================================================
echo "📦 Installing Python deps (FastAPI stack only)..."

$PY -m pip install fastapi uvicorn numpy

echo "✅ Host environment ready"

# =====================================================
# 5. START CAMERA SERVICE
# =====================================================
if [ -f "$HOST_CAM" ]; then
    echo "📷 Starting host camera service..."

    nohup $PY "$HOST_CAM" \
        > "$BASE_DIR/host_camera.log" 2>&1 &

    echo $! > "$PID_FILE"

    sleep 2

    echo "✅ Host camera running"
    echo "🌐 Stream:"
    echo "   http://127.0.0.1:9000/video"
else
    echo "❌ host_camera_service.py not found"
    exit 1
fi

