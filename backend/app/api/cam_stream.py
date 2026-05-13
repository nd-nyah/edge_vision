import cv2
import json
import base64
import time
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.services.detector import Detector
from app.core.config import YOLOV5_MODEL_PATH, YOLO_WORLD_MODEL_PATH
from app.pipelines.pi_pipeline import PiPipeline

router = APIRouter()

# ---------------------------------------------------
# Detector
# ---------------------------------------------------
detector = Detector(
    YOLOV5_MODEL_PATH,
    YOLO_WORLD_MODEL_PATH
)

# ---------------------------------------------------
# Pipeline (handles Pi / fallback camera)
# ---------------------------------------------------
pipeline = PiPipeline()

# ---------------------------------------------------
# Config
# ---------------------------------------------------
JPEG_QUALITY = 70


# ---------------------------------------------------
# Prompt API
# ---------------------------------------------------
@router.post("/set-prompts")
def set_prompts(data: dict):
    prompts = data.get("prompts", [])

    if isinstance(prompts, str):
        prompts = [p.strip() for p in prompts.split(",")]

    detector.set_prompts(prompts)

    print(f"[CAM STREAM] Prompts updated: {prompts}")

    return {
        "status": "ok",
        "prompts": prompts
    }


# ---------------------------------------------------
# Stream Generator
# ---------------------------------------------------
def generate_frames():

    # -----------------------------
    # init camera pipeline
    # -----------------------------
    if not pipeline.init():
        print("[CAM STREAM] Camera not available ❌")

        yield json.dumps({
            "status": "camera_not_found",
            "message": "No camera detected by PI pipeline"
        }) + "\n"

        return

    print("[CAM STREAM] Camera pipeline started successfully ✅")

    frame_idx = 0
    last_log = time.time()

    while True:

        frame = pipeline.read()

        if frame is None:
            print("[CAM STREAM] Frame read failed")
            continue

        frame_idx += 1

        # -----------------------------
        # inference
        # -----------------------------
        detections, _ = detector.detect(frame)

        drawn = detector.draw(frame.copy(), detections)

        # -----------------------------
        # encode frame
        # -----------------------------
        success, buffer = cv2.imencode(
            ".jpg",
            drawn,
            [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
        )

        if not success:
            continue

        b64 = base64.b64encode(buffer.tobytes()).decode("utf-8")

        # -----------------------------
        # optional heartbeat log
        # -----------------------------
        if time.time() - last_log > 5:
            print(f"[CAM STREAM] running... frame={frame_idx}")
            last_log = time.time()

        # -----------------------------
        # stream output
        # -----------------------------
        yield json.dumps({
            "image": b64,
            "detections": detections,
            "frame": frame_idx,
            "status": "running"
        }) + "\n"


# ---------------------------------------------------
# Streaming endpoint
# ---------------------------------------------------
@router.get("/camera-stream")
def camera_stream():

    return StreamingResponse(
        generate_frames(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# ---------------------------------------------------
# MJPEG preview (optional)
# ---------------------------------------------------
def mjpeg_generator():

    if not pipeline.init():
        return

    while True:

        frame = pipeline.read()

        if frame is None:
            continue

        success, buffer = cv2.imencode(
            ".jpg",
            frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
        )

        if not success:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            buffer.tobytes() +
            b"\r\n"
        )


@router.get("/camera-preview")
def camera_preview():

    return StreamingResponse(
        mjpeg_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )