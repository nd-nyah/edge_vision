import os
import cv2
import json
import base64
import time
from collections import deque

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

# from picamera2 import Picamera2
try:
    from picamera2 import Picamera2
    PICAMERA_AVAILABLE = True
except Exception:
    PICAMERA_AVAILABLE = False

from detector import Detector

router = APIRouter()

# ---------------------------------------------------
# Models / Setup
# ---------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

YOLOV5_MODEL = os.path.join(BASE_DIR, "models", "yolov5s.onnx")
YOLO_WORLD_MODEL = os.path.join(BASE_DIR, "models", "yolov8s-world.pt")

detector = Detector(YOLOV5_MODEL, YOLO_WORLD_MODEL)

# ---------------------------------------------------
# Config
# ---------------------------------------------------

JPEG_QUALITY = 70
TIME_WINDOW = 0.5
INFERENCE_FPS = 5   # lower for Raspberry Pi stability

object_memory = deque(maxlen=300)

# ---------------------------------------------------
# Camera init (Pi Camera v2)
# ---------------------------------------------------

picam2 = None

if PICAMERA_AVAILABLE:

    picam2 = Picamera2()

    camera_config = picam2.create_video_configuration(
        main={"size": (640, 480), "format": "RGB888"}
    )

    picam2.configure(camera_config)
    picam2.start()

    # warm-up
    time.sleep(1)

# ---------------------------------------------------
# Prompt API
# ---------------------------------------------------

@router.post("/set-prompts")
def set_prompts(data: dict):
    prompts = data.get("prompts", [])

    if isinstance(prompts, str):
        prompts = [p.strip() for p in prompts.split(",")]

    detector.set_prompts(prompts)

    return {"status": "ok", "prompts": prompts}

# ---------------------------------------------------
# Helpers
# ---------------------------------------------------

def make_id(d):
    x = int(d["bbox"]["x"] // 30)
    y = int(d["bbox"]["y"] // 30)
    return f"{d['label']}_{x}_{y}"

# ---------------------------------------------------
# Stream generator (Pi Camera v2)
# ---------------------------------------------------

def generate_frames():
    assert picam2 is not None

      # -----------------------------------------
    # camera availability guard
    # -----------------------------------------
    if not PICAMERA_AVAILABLE:
        yield json.dumps({
            "error": "Pi Camera unavailable on this system"
        }) + "\n"
        return
    
    frame_idx = 0
    last_inference_time = 0

    BATCH_SIZE = 4
    batch_frames = []

    while True:
        # Capture frame from Pi Camera
        frame = picam2.capture_array()

        frame_idx += 1
        now = time.time()

        # ---------------------------------------------------
        # FPS control
        # ---------------------------------------------------
        if now - last_inference_time < 1.0 / INFERENCE_FPS:
            continue

        # ---------------------------------------------------
        # add frame to batch
        # ---------------------------------------------------
        batch_frames.append((frame, now, frame_idx))

        # wait until batch is full
        if len(batch_frames) < BATCH_SIZE:
            continue

        last_inference_time = now

        # ---------------------------------------------------
        # PROCESS BATCH (ONLY CHANGE)
        # ---------------------------------------------------
        for frame, now, frame_idx in batch_frames:

            detections, _ = detector.detect(frame)

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

            drawn = detector.draw(frame.copy(), visible_objects)

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
                "frame": frame_idx,
                "timestamp": now
            }) + "\n"

        # ---------------------------------------------------
        # reset batch
        # ---------------------------------------------------
        batch_frames = []
# ---------------------------------------------------
# MJPEG Preview Generator
# ---------------------------------------------------

def mjpeg_generator():

    if not PICAMERA_AVAILABLE or picam2 is None:
        return

    while True:

        frame = picam2.capture_array()

        success, buffer = cv2.imencode(
            ".jpg",
            frame,
            [
                int(cv2.IMWRITE_JPEG_QUALITY),
                JPEG_QUALITY
            ]
        )

        if not success:
            continue

        jpg_bytes = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            jpg_bytes +
            b"\r\n"
        )

# ---------------------------------------------------
# Detection Stream Endpoint
# ---------------------------------------------------

@router.get("/camera-stream")
def camera_stream():

    return StreamingResponse(
        generate_frames(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

# ---------------------------------------------------
# Live Preview Endpoint
# ---------------------------------------------------

@router.get("/camera-preview")
def camera_preview():

    return StreamingResponse(
        mjpeg_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

# # -------------------------------------------------------
# # ver 1.2
# # -------------------------------------------------------
# import os
# import cv2
# import json
# import base64
# import time

# from collections import deque

# from fastapi import APIRouter
# from fastapi.responses import StreamingResponse

# # ---------------------------------------------------
# # Pi Camera Import
# # ---------------------------------------------------

# try:
#     from picamera2 import Picamera2
#     PICAMERA_AVAILABLE = True
# except Exception:
#     PICAMERA_AVAILABLE = False

# from detector import Detector

# router = APIRouter()

# # ---------------------------------------------------
# # Models / Setup
# # ---------------------------------------------------

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# YOLOV5_MODEL = os.path.join(
#     BASE_DIR,
#     "models",
#     "yolov5s.onnx"
# )

# YOLO_WORLD_MODEL = os.path.join(
#     BASE_DIR,
#     "models",
#     "yolov8s-world.pt"
# )

# detector = Detector(
#     YOLOV5_MODEL,
#     YOLO_WORLD_MODEL
# )

# # ---------------------------------------------------
# # Config
# # ---------------------------------------------------

# JPEG_QUALITY = 70
# TIME_WINDOW = 0.5
# INFERENCE_FPS = 5

# object_memory = deque(maxlen=300)

# # ---------------------------------------------------
# # Camera Init
# # ---------------------------------------------------

# picam2 = None

# if PICAMERA_AVAILABLE:

#     picam2 = Picamera2()

#     camera_config = picam2.create_video_configuration(
#         main={
#             "size": (640, 480),
#             "format": "RGB888"
#         }
#     )

#     picam2.configure(camera_config)

#     picam2.start()

#     # warm-up
#     time.sleep(1)

# # ---------------------------------------------------
# # Prompt API
# # ---------------------------------------------------

# @router.post("/set-prompts")
# def set_prompts(data: dict):

#     prompts = data.get("prompts", [])

#     if isinstance(prompts, str):
#         prompts = [
#             p.strip()
#             for p in prompts.split(",")
#         ]

#     detector.set_prompts(prompts)

#     return {
#         "status": "ok",
#         "prompts": prompts
#     }

# # ---------------------------------------------------
# # Helpers
# # ---------------------------------------------------

# def make_id(d):

#     x = int(d["bbox"]["x"] // 30)
#     y = int(d["bbox"]["y"] // 30)

#     return f"{d['label']}_{x}_{y}"

# # ---------------------------------------------------
# # Detection Stream Generator
# # ---------------------------------------------------

# def generate_frames():

#     # -----------------------------------------
#     # camera availability guard
#     # -----------------------------------------

#     if not PICAMERA_AVAILABLE or picam2 is None:

#         yield json.dumps({
#             "error": "Pi Camera unavailable on this system"
#         }) + "\n"

#         return

#     frame_idx = 0
#     last_inference_time = 0

#     BATCH_SIZE = 4
#     batch_frames = []

#     while True:

#         # -----------------------------------------
#         # Capture frame
#         # -----------------------------------------

#         frame = picam2.capture_array()

#         frame_idx += 1

#         now = time.time()

#         # -----------------------------------------
#         # FPS throttle
#         # -----------------------------------------

#         if now - last_inference_time < 1.0 / INFERENCE_FPS:
#             continue

#         # -----------------------------------------
#         # Add to batch
#         # -----------------------------------------

#         batch_frames.append(
#             (frame, now, frame_idx)
#         )

#         if len(batch_frames) < BATCH_SIZE:
#             continue

#         last_inference_time = now

#         # -----------------------------------------
#         # Process batch
#         # -----------------------------------------

#         for frame, now, frame_idx in batch_frames:

#             detections, _ = detector.detect(frame)

#             # -----------------------------------------
#             # memory smoothing
#             # -----------------------------------------

#             for d in detections:

#                 object_memory.append({
#                     "id": make_id(d),
#                     "data": d,
#                     "time": now
#                 })

#             visible_objects = [
#                 x["data"]
#                 for x in object_memory
#                 if now - x["time"] < TIME_WINDOW
#             ]

#             # -----------------------------------------
#             # draw detections
#             # -----------------------------------------

#             drawn = detector.draw(
#                 frame.copy(),
#                 visible_objects
#             )

#             # -----------------------------------------
#             # encode jpg
#             # -----------------------------------------

#             success, buffer = cv2.imencode(
#                 ".jpg",
#                 drawn,
#                 [
#                     int(cv2.IMWRITE_JPEG_QUALITY),
#                     JPEG_QUALITY
#                 ]
#             )

#             if not success:
#                 continue

#             b64 = base64.b64encode(
#                 buffer.tobytes()
#             ).decode("utf-8")

#             # -----------------------------------------
#             # stream json line
#             # -----------------------------------------

#             yield json.dumps({
#                 "image": b64,
#                 "detections": visible_objects,
#                 "frame": frame_idx,
#                 "timestamp": now
#             }) + "\n"

#         # -----------------------------------------
#         # reset batch
#         # -----------------------------------------

#         batch_frames = []

# # ---------------------------------------------------
# # MJPEG Preview Generator
# # ---------------------------------------------------

# def mjpeg_generator():

#     if not PICAMERA_AVAILABLE or picam2 is None:
#         return

#     while True:

#         frame = picam2.capture_array()

#         success, buffer = cv2.imencode(
#             ".jpg",
#             frame,
#             [
#                 int(cv2.IMWRITE_JPEG_QUALITY),
#                 JPEG_QUALITY
#             ]
#         )

#         if not success:
#             continue

#         jpg_bytes = buffer.tobytes()

#         yield (
#             b"--frame\r\n"
#             b"Content-Type: image/jpeg\r\n\r\n" +
#             jpg_bytes +
#             b"\r\n"
#         )

# # ---------------------------------------------------
# # Detection Stream Endpoint
# # ---------------------------------------------------

# @router.get("/camera-stream")
# def camera_stream():

#     return StreamingResponse(
#         generate_frames(),
#         media_type="text/plain",
#         headers={
#             "Cache-Control": "no-cache",
#             "Connection": "keep-alive",
#             "X-Accel-Buffering": "no",
#         }
#     )

# # ---------------------------------------------------
# # Live Preview Endpoint
# # ---------------------------------------------------

# @router.get("/camera-preview")
# def camera_preview():

#     return StreamingResponse(
#         mjpeg_generator(),
#         media_type="multipart/x-mixed-replace; boundary=frame"
#     )