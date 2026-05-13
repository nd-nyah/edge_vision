import os
import cv2
import json
import base64
import time
from collections import deque
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.services.detector import Detector
from app.core.config import YOLOV5_MODEL_PATH, YOLO_WORLD_MODEL_PATH,VIDEO_DIR

router = APIRouter()

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# VIDEO_DIR = os.path.join(BASE_DIR, "video")

# YOLOV5_MODEL = os.path.join(BASE_DIR, "models", "yolov5s.onnx")
# YOLO_WORLD_MODEL = os.path.join(BASE_DIR, "models", "yolov8s-world.pt")

# BASE_DIR = Path(__file__).resolve().parents[2]  # app/services -> app -> backend/app

# VIDEO_DIR = BASE_DIR / "video"

# YOLOV5_MODEL = BASE_DIR / "models" / "yolov5s.onnx"
# YOLO_WORLD_MODEL = BASE_DIR / "models" / "yolov8s-world.pt"

detector = Detector(
    YOLOV5_MODEL_PATH,
    YOLO_WORLD_MODEL_PATH
)

BATCH_SIZE = 4
JPEG_QUALITY = 70
TIME_WINDOW = 0.5

object_memory = deque(maxlen=300)

def get_video():
    files = sorted(f for f in os.listdir(VIDEO_DIR) if f.endswith(".mp4"))
    if not files:
        raise HTTPException(status_code=404, detail="No video found")
    return os.path.join(VIDEO_DIR, files[0])

@router.post("/set-prompts")
def set_prompts(data: dict):
    prompts = data.get("prompts", [])

    if isinstance(prompts, str):
        prompts = [p.strip() for p in prompts.split(",")]

    detector.set_prompts(prompts)

    return {
        "status": "ok",
        "prompts": prompts
    }

def make_id(d):
    x = int(d["bbox"]["x"] // 30)
    y = int(d["bbox"]["y"] // 30)
    return f"{d['label']}_{x}_{y}"

def generate_frames():
    video_path = get_video()
    cap = cv2.VideoCapture(video_path)

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_idx = 0

    buffer_frames = []
    raw_frames = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1
        now = time.time()

        buffer_frames.append(frame)
        raw_frames.append(frame)

        if len(buffer_frames) < BATCH_SIZE:
            continue

        for f in raw_frames:

            detections, _ = detector.detect(f)

            for d in detections:
                object_memory.append({
                    "id": make_id(d),
                    "data": d,
                    "time": now
                })

            visible_objects = [
                x["data"]
                for x in object_memory
                if now - x["time"] < TIME_WINDOW
            ]

            drawn = detector.draw(f.copy(), visible_objects)

            success, buffer = cv2.imencode(
                ".jpg",
                drawn,
                [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
            )

            if not success:
                continue

            b64 = base64.b64encode(buffer.tobytes()).decode("utf-8")

            progress = round((frame_idx / total_frames) * 100, 2)

            yield json.dumps({
                "image": b64,
                "detections": visible_objects,
                "progress": progress
            }) + "\n"

        buffer_frames = []
        raw_frames = []

    cap.release()

    yield json.dumps({
        "status": "done",
        "progress": 100
    }) + "\n"

@router.get("/video")
def stream_video():
    return StreamingResponse(
        generate_frames(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

