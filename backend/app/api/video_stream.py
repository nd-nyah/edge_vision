import os
import cv2
import json
import base64

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.services.detector import Detector
from app.pipelines.video_detector_pipeline import DetectorPipeline

from app.core.config import (
    YOLOV5_MODEL_PATH,
    YOLO_WORLD_MODEL_PATH,
    VIDEO_DIR
)

router = APIRouter()

detector = Detector(
    YOLOV5_MODEL_PATH,
    YOLO_WORLD_MODEL_PATH
)

pipeline = DetectorPipeline(detector)

BATCH_SIZE = 32
JPEG_QUALITY = 70


def get_video():

    files = sorted(
        f for f in os.listdir(VIDEO_DIR)
        if f.endswith(".mp4")
    )

    if not files:
        raise HTTPException(
            status_code=404,
            detail="No video found"
        )

    return os.path.join(VIDEO_DIR, files[0])


@router.post("/set-prompts")
def set_prompts(data: dict):

    prompts = data.get("prompts", [])

    if isinstance(prompts, str):
        prompts = [
            p.strip()
            for p in prompts.split(",")
        ]

    detector.set_prompts(prompts)

    return {
        "status": "ok",
        "prompts": prompts
    }


def generate_frames():

    video_path = get_video()

    cap = cv2.VideoCapture(video_path)

    total_frames = int(
        cap.get(cv2.CAP_PROP_FRAME_COUNT)
    )

    frame_idx = 0

    buffer_frames = []

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        frame_idx += 1

        buffer_frames.append(frame)

        if len(buffer_frames) == BATCH_SIZE:
            continue

        for f in buffer_frames:

            result = pipeline.process_frame(
                f,
                frame_idx
            )

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

            b64 = base64.b64encode(
                buffer.tobytes()
            ).decode("utf-8")

            progress = round(
                (frame_idx / total_frames) * 100,
                2
            )

            yield json.dumps({
                "image": b64,
                "detections": detections,
                "fps": fps,
                "mode": mode,
                "progress": progress
            }) + "\n"

        buffer_frames = []

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


@router.get("/video-preview")
def video_preview():

    files = sorted(
        f for f in os.listdir(VIDEO_DIR)
        if f.endswith(".mp4")
    )

    if not files:
        raise HTTPException(
            status_code=404,
            detail="No video found"
        )

    video_path = os.path.join(
        VIDEO_DIR,
        files[0]
    )

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise HTTPException(
            status_code=500,
            detail="Unable to open video"
        )

    ret, frame = cap.read()

    cap.release()

    if not ret or frame is None:
        raise HTTPException(
            status_code=500,
            detail="Unable to read video frame"
        )

    success, buffer = cv2.imencode(
        ".jpg",
        frame,
        [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
    )

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to encode preview"
        )

    return StreamingResponse(
        iter([buffer.tobytes()]),
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


