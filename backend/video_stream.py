import os
import cv2
import json
import base64
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from detector import Detector

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_DIR = os.path.join(BASE_DIR, "video")
MODEL_PATH = os.path.join(BASE_DIR, "models", "yolov5s.onnx")

detector = Detector(MODEL_PATH)

BATCH_SIZE = 4  # optional, keep small for responsiveness


def get_video():
    files = [f for f in os.listdir(VIDEO_DIR) if f.endswith(".mp4")]
    if not files:
        raise HTTPException(status_code=404, detail="No video found")

    return os.path.join(VIDEO_DIR, files[0])


def generate_frames():
    print("🔥 STREAM STARTED")

    video_path = get_video()
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise RuntimeError("Failed to open video")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"🎞 TOTAL FRAMES: {total_frames}")

    frame_idx = 0

    batch = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1
        batch.append(frame)

        # =========================
        # PROCESS IMMEDIATELY (OR BATCH)
        # =========================
        detections, drawn = detector.detect(frame)

        # encode frame
        success, buffer = cv2.imencode(".jpg", drawn)
        if not success:
            continue

        b64 = base64.b64encode(buffer.tobytes()).decode("utf-8")

        # =========================
        # REAL PROGRESS (KEY FIX)
        # =========================
        progress = round((frame_idx / total_frames) * 100, 2)

        # =========================
        # STREAM FRAME IMMEDIATELY
        # =========================
        yield json.dumps({
            "image": b64,
            "detections": detections,
            "progress": progress
        }) + "\n"

        print(f"📦 FRAME {frame_idx}/{total_frames} | {progress}%")

    cap.release()

    # =========================
    # FINAL SIGNAL
    # =========================
    yield json.dumps({
        "status": "detection_completed",
        "progress": 100.0
    }) + "\n"

    print("✅ DETECTION COMPLETED")


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