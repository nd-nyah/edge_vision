import os
import cv2
import json
import base64
import time

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.services.detector import Detector
from app.pipelines.video_detector_pipeline import DetectorPipeline

from app.core.config import (
    YOLOV5_MODEL_PATH,
    YOLO_WORLD_MODEL_PATH,
    CAMERA_DIR
)

router = APIRouter()

detector = Detector(
    YOLOV5_MODEL_PATH,
    YOLO_WORLD_MODEL_PATH
)

pipeline = DetectorPipeline(detector)

BATCH_SIZE = 32
JPEG_QUALITY = 70


# --------------------------------------------------
# GET LATEST STABLE CAMERA FILE
# --------------------------------------------------

def get_latest_camera():

    if not os.path.exists(CAMERA_DIR):
        raise HTTPException(status_code=404, detail="Camera directory not found")

    files = [
        f for f in os.listdir(CAMERA_DIR)
        if f.endswith(".mp4")
    ]

    if not files:
        raise HTTPException(status_code=404, detail="No camera recording found")

    # sort by modified time (most reliable)
    files = sorted(
        files,
        key=lambda x: os.path.getmtime(os.path.join(CAMERA_DIR, x))
    )

    latest_file = os.path.join(CAMERA_DIR, files[-1])

    # avoid reading file while still being written
    size1 = os.path.getsize(latest_file)
    time.sleep(0.3)
    size2 = os.path.getsize(latest_file)

    if size1 != size2:
        raise HTTPException(
            status_code=503,
            detail="Camera recording still being written"
        )

    return latest_file


# --------------------------------------------------
# SET PROMPTS
# --------------------------------------------------

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


# --------------------------------------------------
# CAMERA STREAM (ANALYTICS PIPELINE)
# --------------------------------------------------

def generate_frames():

    camera_path = get_latest_camera()

    cap = cv2.VideoCapture(camera_path)

    if not cap.isOpened():
        raise HTTPException(status_code=500, detail="Unable to open camera file")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1

    frame_idx = 0
    buffer_frames = []

    try:

        while True:

            ret, frame = cap.read()

            if not ret:
                break

            frame_idx += 1
            buffer_frames.append(frame)

            if len(buffer_frames) < BATCH_SIZE:
                continue

            for f in buffer_frames:

                result = pipeline.process_frame(f, frame_idx)

                drawn = result["frame"]
                detections = result["detections"]
                fps = result["fps"]
                mode = result["mode"]

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
                    "detections": detections,
                    "fps": fps,
                    "mode": mode,
                    "progress": progress
                }) + "\n"

            buffer_frames = []

    finally:
        cap.release()

    yield json.dumps({
        "status": "done",
        "progress": 100
    }) + "\n"


# --------------------------------------------------
# CAMERA STREAM ENDPOINT
# --------------------------------------------------

@router.get("/camera")
def stream_camera():

    return StreamingResponse(
        generate_frames(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# --------------------------------------------------
# CAMERA PREVIEW ENDPOINT
# --------------------------------------------------

@router.get("/camera-preview")
def camera_preview():

    camera_path = get_latest_camera()

    cap = cv2.VideoCapture(camera_path)

    if not cap.isOpened():
        raise HTTPException(status_code=500, detail="Unable to open camera file")

    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        raise HTTPException(status_code=500, detail="Unable to read frame")

    success, buffer = cv2.imencode(
        ".jpg",
        frame,
        [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
    )

    if not success:
        raise HTTPException(status_code=500, detail="JPEG encode failed")

    return StreamingResponse(
        iter([buffer.tobytes()]),
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )
