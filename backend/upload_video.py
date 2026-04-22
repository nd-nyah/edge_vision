import os
import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter()

# =========================
# FIXED VIDEO FOLDER
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_DIR = os.path.join(BASE_DIR, "video")

os.makedirs(VIDEO_DIR, exist_ok=True)

# =========================
# UPLOAD VIDEO
# =========================
@router.post("/upload-video")
async def upload_video(file: UploadFile = File(...)):

    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")

    print("🔥 REQUEST HIT:", file.filename)

    safe_name = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(VIDEO_DIR, safe_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    print("✅ SAVED:", file_path)

    return {
        "status": "success",
        "filename": safe_name
    }

# =========================
# DELETE VIDEO
# =========================
@router.delete("/delete-video")
async def delete_video(filename: str):

    file_path = os.path.join(VIDEO_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    os.remove(file_path)

    print("🗑 DELETED:", file_path)

    return {"status": "success"}