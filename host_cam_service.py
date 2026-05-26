import cv2
import time
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

# =========================
# CSI CAMERA PIPELINE
# =========================
PIPELINE = (
    "nvarguscamerasrc sensor-id=0 ! "
    "video/x-raw(memory:NVMM), width=1280, height=720, framerate=30/1 ! "
    "nvvidconv ! video/x-raw, format=BGRx ! "
    "videoconvert ! video/x-raw, format=BGR ! "
    "appsink drop=true max-buffers=1 sync=false"
)

cap = cv2.VideoCapture(PIPELINE, cv2.CAP_GSTREAMER)

if not cap.isOpened():
    raise RuntimeError("[HOST CAMERA] Failed to open CSI camera")


def generate_frames():

    while True:

        ret, frame = cap.read()
        if not ret:
            time.sleep(0.01)
            continue

        ok, jpeg = cv2.imencode(
            ".jpg",
            frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), 70]
        )

        if not ok:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            jpeg.tobytes() +
            b"\r\n"
        )


# =========================
# MJPEG ENDPOINT
# =========================
@app.get("/video")
def video_stream():

    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


# =========================
# HEALTH CHECK
# =========================
@app.get("/health")
def health():
    return {"status": "ok"}