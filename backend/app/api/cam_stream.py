import os
import cv2
import json
import base64
import time
from collections import deque
from threading import Thread, Lock, Event

from fastapi import APIRouter
from fastapi.responses import StreamingResponse, Response

from app.services.detector import Detector
from app.core.config import (
    YOLOV5_MODEL_PATH,
    YOLO_WORLD_MODEL_PATH,
)

router = APIRouter()

detector = Detector(
    YOLOV5_MODEL_PATH,
    YOLO_WORLD_MODEL_PATH
)

# =========================
# CONFIG
# =========================
BATCH_SIZE = 4
JPEG_QUALITY = 70
TIME_WINDOW = 0.5

object_memory = deque(maxlen=300)

# =========================
# CAMERA SHARED STATE
# =========================
latest_frame = None
frame_lock = Lock()
frame_ready = Event()

camera_started = False


# =========================
# BUFFER DIR (optional only)
# =========================
CAM_BUFFER_DIR = os.path.join(os.getcwd(), "camera_buffer")
os.makedirs(CAM_BUFFER_DIR, exist_ok=True)

print(f"[CONFIG] CAMERA BUFFER = {CAM_BUFFER_DIR}")


# =========================
# GSTREAMER PIPELINE
# =========================
def gstreamer_pipeline(
    sensor_id=0,
    capture_width=1280,
    capture_height=720,
    framerate=30,
    flip_method=0,
):
    return (
        "nvarguscamerasrc sensor-id=%d ! "
        "video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! "
        "appsink drop=1 sync=false"
        % (
            sensor_id,
            capture_width,
            capture_height,
            framerate,
            flip_method,
        )
    )


# =========================
# CAMERA WORKER (ONLY ONE OPENCV INSTANCE)
# =========================
def camera_worker():
    global latest_frame

    print("[CAMERA] Starting single CSI worker...")

    cap = cv2.VideoCapture(
        gstreamer_pipeline(),
        cv2.CAP_GSTREAMER
    )

    if not cap.isOpened():
        print("[ERROR] CSI camera failed to open")
        return

    # warmup
    for _ in range(5):
        cap.read()

    while True:
        ret, frame = cap.read()

        if not ret:
            continue

        with frame_lock:
            latest_frame = frame
            frame_ready.set()


# =========================
# START CAMERA ONLY ONCE
# =========================
def start_camera():
    global camera_started

    if camera_started:
        return

    camera_started = True
    Thread(target=camera_worker, daemon=True).start()
    print("[CAMERA] Worker started")


# =========================
# PROMPTS
# =========================
@router.post("/set-prompts")
def set_prompts(data: dict):
    prompts = data.get("prompts", [])

    if isinstance(prompts, str):
        prompts = [p.strip() for p in prompts.split(",")]

    detector.set_prompts(prompts)

    return {"status": "ok", "prompts": prompts}


# =========================
# FRAME ID
# =========================
def make_id(d):
    x = int(d["bbox"]["x"] // 30)
    y = int(d["bbox"]["y"] // 30)
    return f"{d['label']}_{x}_{y}"


# =========================
# STREAM (BATCH INFERENCE)
# =========================
def generate_frames():
    start_camera()

    global latest_frame

    frame_idx = 0
    raw_frames = []

    while True:

        frame_ready.wait()

        with frame_lock:
            if latest_frame is None:
                continue
            frame = latest_frame.copy()

        frame_idx += 1
        now = time.time()

        raw_frames.append(frame)

        if len(raw_frames) < BATCH_SIZE:
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

            yield json.dumps({
                "image": b64,
                "detections": visible_objects,
                "frame": frame_idx
            }) + "\n"

        raw_frames = []


# =========================
# STREAM ENDPOINT
# =========================
@router.get("/camera-stream")
def camera_stream():
    print("[STREAM] camera-stream started")

    return StreamingResponse(
        generate_frames(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# =========================
# PREVIEW (TEXT ONLY - SAFE)
# =========================
@router.get("/camera-preview")
def camera_preview():

    start_camera()

    if not frame_ready.wait(timeout=3):
        return Response(
            content="CAMERA WARMING UP... STREAM IN PROGRESS",
            media_type="text/plain"
        )

    return Response(
        content="LIVE STREAM IN PROGRESS",
        media_type="text/plain"
    )

