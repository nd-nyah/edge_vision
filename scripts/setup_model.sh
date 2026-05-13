#!/bin/bash

set -e

echo "📦 Setting up YOLO model..."

# -----------------------------
# Paths
# -----------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Project root = one level above scripts/
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# NEW STRUCTURE
MODEL_DIR="$PROJECT_ROOT/backend/app/models"
MODEL_PATH="$MODEL_DIR/yolov5s.onnx"

echo "📁 Project root: $PROJECT_ROOT"
echo "📁 Model path: $MODEL_PATH"

# -----------------------------
# Create model directory
# -----------------------------
mkdir -p "$MODEL_DIR"

# -----------------------------
# Download model
# -----------------------------
if [ -f "$MODEL_PATH" ]; then
    echo "✅ Model already exists"
else
    echo "⬇️ Downloading YOLOv5 ONNX model..."

    wget -q --show-progress \
        https://github.com/ultralytics/yolov5/releases/download/v6.0/yolov5s.onnx \
        -O "$MODEL_PATH"

    echo "✅ Download complete"
fi

# -----------------------------
# Verify model
# -----------------------------
echo "🔍 Verifying ONNX model..."

python3 - <<EOF
import onnxruntime as ort

path = "$MODEL_PATH"

ort.InferenceSession(path)

print("✅ ONNX model is valid")
EOF

echo "🎉 Setup finished successfully!"


# #!/bin/bash

# set -e

# echo "📦 Setting up YOLO model..."

# # 🔥 Get script directory (scripts/)
# SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# # 🔥 Project root = one level above scripts/
# PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# # 📁 Models folder (correct path)
# MODEL_DIR="$PROJECT_ROOT/models"
# MODEL_PATH="$MODEL_DIR/yolov5s.onnx"

# echo "📁 Project root: $PROJECT_ROOT"
# echo "📁 Model path: $MODEL_PATH"

# # Create models folder if not exists
# mkdir -p "$MODEL_DIR"

# # Download model if missing
# if [ -f "$MODEL_PATH" ]; then
#     echo "✅ Model already exists"
# else
#     echo "⬇️ Downloading YOLOv5 ONNX model..."

#     wget -q --show-progress \
#         https://github.com/ultralytics/yolov5/releases/download/v6.0/yolov5s.onnx \
#         -O "$MODEL_PATH"

#     echo "✅ Download complete"
# fi

# # Verify model loads
# echo "🔍 Verifying ONNX model..."

# python3 - <<EOF
# import onnxruntime as ort

# path = "$MODEL_PATH"
# ort.InferenceSession(path)
# print("✅ ONNX model is valid")
# EOF

# echo "🎉 Setup finished successfully!"