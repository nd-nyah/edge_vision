import time
from fastapi import APIRouter
from fastapi.responses import StreamingResponse, Response

from app.pipelines.jetson_detector_pipeline import JetsonDetectorPipeline
from app.services.detector import Detector
from app.core.config import (
    YOLOV5_MODEL_PATH,
    YOLO_WORLD_MODEL_PATH,
)

router = APIRouter()

# =========================
# INIT
# =========================
detector = Detector(
    YOLOV5_MODEL_PATH,
    YOLO_WORLD_MODEL_PATH
)

pipeline = JetsonDetectorPipeline(detector)

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
    print("[STREAM] Jetson pipeline started")


# =========================
# MJPEG STREAM (OPTIMIZED)
# =========================
def generate_frames():
    start_pipeline()

    while True:

        jpeg = pipeline.get_jpeg()

        if jpeg is None:
            time.sleep(0.01)
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
        return Response(
            content="CAMERA WARMING UP...",
            media_type="text/plain"
        )

    return Response(
        content="LIVE STREAM ACTIVE",
        media_type="text/plain"
    )