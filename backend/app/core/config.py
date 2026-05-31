import os

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# => backend/app

BACKEND_DIR = os.path.dirname(APP_DIR)
# => backend

MODEL_DIR = os.path.join(APP_DIR, "models")

YOLOV5_MODEL_PATH = os.path.join(MODEL_DIR, "yolov5s.onnx")
YOLO_WORLD_MODEL_PATH = os.path.join(MODEL_DIR, "yolov8s-world.pt")

VIDEO_DIR = os.path.join(BACKEND_DIR, "video")
CAMERA_DIR = os.path.join(BACKEND_DIR, "data", "camera")