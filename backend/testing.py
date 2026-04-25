import os
import cv2
from fastapi import HTTPException

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_DIR = os.path.join(BASE_DIR, "video")
def get_video():
    files = [f for f in os.listdir(VIDEO_DIR) if f.endswith(".mp4")]

    if not files:
        raise HTTPException(status_code=404, detail="No video uploaded")

    return os.path.join(VIDEO_DIR, files[0])

cap = cv2.VideoCapture(get_video())
print("OPEN:", cap.isOpened())

ret, frame = cap.read()
print("FIRST FRAME:", ret)