#!/bin/bash

set -e

echo "🚀 Setting up YOLO Prompt / YOLO-World Model..."

# -----------------------------
# Paths
# -----------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# NEW STRUCTURE
MODEL_DIR="$PROJECT_ROOT/backend/app/models"
MODEL_PATH="$MODEL_DIR/yolov8s-world.pt"

mkdir -p "$MODEL_DIR"

echo "📁 Model directory: $MODEL_DIR"

# -----------------------------
# Download YOLO-World model
# -----------------------------
if [ -f "$MODEL_PATH" ]; then
    echo "✅ Model already exists: yolov8s-world.pt"
else
    echo "⬇️ Downloading YOLO-World model..."

    wget -q --show-progress \
        https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8s-world.pt \
        -O "$MODEL_PATH"

    echo "✅ Download complete"
fi

# -----------------------------
# Verify file
# -----------------------------
echo "🔍 Verifying model..."

if [ -s "$MODEL_PATH" ]; then
    echo "✅ Model ready at: $MODEL_PATH"
    echo "📦 Size: $(du -h "$MODEL_PATH" | cut -f1)"
else
    echo "❌ Model download failed or file is empty"
    exit 1
fi

echo "🎉 YOLO-World setup complete!"

# #!/bin/bash

# set -e

# echo "🚀 Setting up YOLO Prompt / YOLO-World Model..."

# # -----------------------------
# # Paths
# # -----------------------------
# SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# MODEL_DIR="$PROJECT_ROOT/backend/models"
# MODEL_PATH="$MODEL_DIR/yolov8s-world.pt"

# mkdir -p "$MODEL_DIR"

# echo "📁 Model directory: $MODEL_DIR"

# # -----------------------------
# # Download YOLO-World model
# # -----------------------------
# if [ -f "$MODEL_PATH" ]; then
#     echo "✅ Model already exists: yolov8s-world.pt"
# else
#     echo "⬇️ Downloading YOLO-World model..."

#     wget -q --show-progress \
#         https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8s-world.pt \
#         -O "$MODEL_PATH"

#     echo "✅ Download complete"
# fi

# # -----------------------------
# # Verify file
# # -----------------------------
# echo "🔍 Verifying model..."

# if [ -s "$MODEL_PATH" ]; then
#     echo "✅ Model ready at: $MODEL_PATH"
#     echo "📦 Size: $(du -h "$MODEL_PATH" | cut -f1)"
# else
#     echo "❌ Model download failed or file is empty"
#     exit 1
# fi

# echo "🎉 YOLO-World setup complete!"