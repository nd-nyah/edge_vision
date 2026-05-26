import time
import cv2
import os
from fastapi import APIRouter
from fastapi.responses import StreamingResponse, Response

from app.pipelines.jetson_detector_pipeline import JetsonDetectorPipeline
from app.services.detector import Detector
from app.core.config import YOLOV5_MODEL_PATH, YOLO_WORLD_MODEL_PATH

router = APIRouter()

# =========================
# DETECTOR + PIPELINE
# =========================
detector = Detector(
    YOLOV5_MODEL_PATH,
    YOLO_WORLD_MODEL_PATH
)

pipeline = JetsonDetectorPipeline(detector)

CAMERA_URL = os.getenv(
    "CAMERA_URL",
    "http://127.0.0.1:9000/video"
)

pipeline_started = False


# =========================
# START PIPELINE
# =========================
def start_pipeline():
    global pipeline_started

    if pipeline_started:
        return

    pipeline_started = True
    pipeline.start()
    print("[STREAM] Pipeline started")


# =========================
# CAMERA FEED LOOP
# =========================
def generate_frames():

    start_pipeline()

    cap = cv2.VideoCapture(CAMERA_URL)

    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera stream: {CAMERA_URL}")

    while True:

        ret, frame = cap.read()

        if not ret:
            time.sleep(0.01)
            continue

        output = pipeline.process_frame(frame)

        jpeg = pipeline.get_jpeg()

        if jpeg is None:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            jpeg +
            b"\r\n"
        )


# =========================
# STREAM ENDPOINT
# =========================
@router.get("/camera-stream")
def camera_stream():

    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# =========================
# PREVIEW
# =========================
@router.get("/camera-preview")
def camera_preview():

    start_pipeline()

    output = pipeline.get_latest_output()

    if output is None:
        return Response("WARMING UP...", media_type="text/plain")

    return Response(
        f"LIVE\nFPS: {output.get('fps', 0)}",
        media_type="text/plain"
    )