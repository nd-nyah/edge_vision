import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.core.config import VIDEO_DIR

router = APIRouter()

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# VIDEO_DIR = os.path.join(BASE_DIR, "video")
# from app.core.config import YOLOV5_MODEL_PATH, YOLO_WORLD_MODEL_PATH,VIDEO_DIR

os.makedirs(VIDEO_DIR, exist_ok=True)


def clear_video_folder():
    for f in os.listdir(VIDEO_DIR):
        if f.endswith(".mp4"):
            try:
                os.remove(os.path.join(VIDEO_DIR, f))
            except Exception as e:
                print("delete failed:", e)


@router.post("/upload-video")
async def upload_video(file: UploadFile = File(...)):

    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")

    clear_video_folder()

    safe_name = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(VIDEO_DIR, safe_name)

    try:
        # ✅ STREAMING WRITE (NO HANG)
        with open(file_path, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)  # 1MB
                if not chunk:
                    break
                f.write(chunk)

        await file.close()

        return {
            "status": "success",
            "filename": safe_name
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))