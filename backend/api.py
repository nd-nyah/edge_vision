from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
import numpy as np
import cv2
import tempfile

from backend.config import get_detector

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/detect")
async def detect(file: UploadFile = File(...), detector=Depends(get_detector)):
    content_type = file.content_type

    try:
        data = await file.read()

        # ---------------- IMAGE ----------------
        if content_type.startswith("image/"):
            nparr = np.frombuffer(data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is None:
                raise HTTPException(400, "Invalid image")

            results = detector.predict(frame)

            return {
                "type": "image",
                "results": results
            }

        # ---------------- VIDEO ----------------
        elif content_type.startswith("video/"):

            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp.write(data)
                temp_path = tmp.name

            cap = cv2.VideoCapture(temp_path)

            results_all = []
            frame_count = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                results = detector.predict(frame)
                results_all.append(results)
                frame_count += 1

            cap.release()

            return {
                "type": "video",
                "frames_processed": frame_count,
                "results": results_all[:10]  # limit output
            }

        else:
            raise HTTPException(400, "Unsupported file type")

    except Exception as e:
        raise HTTPException(500, str(e))