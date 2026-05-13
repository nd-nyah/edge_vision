import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.target import TARGET

from app.api.upload_video import router as upload_router
from app.api.video_stream import router as video_router
from app.api.cam_stream import router as cam_router

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_DIR = os.path.join(BASE_DIR, "video")

os.makedirs(VIDEO_DIR, exist_ok=True)

# =========================
# LOG
# =========================
print(f"[BOOT] TARGET = {TARGET}")

# =========================
# CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# ROUTING (CLEAN + MUTUALLY EXCLUSIVE)
# =========================
if TARGET == "pc":
    print("[ROUTES] PC mode: upload + video stream")

    app.include_router(upload_router, prefix="/api")
    app.include_router(video_router, prefix="/api")

    app.mount(
        "/videos",
        StaticFiles(directory=VIDEO_DIR),
        name="videos"
    )

elif TARGET in ["pi", "jetson"]:
    print("[ROUTES] EDGE mode: camera stream")

    app.include_router(cam_router, prefix="/api")

else:
    raise ValueError(f"Invalid TARGET: {TARGET}")

# =========================
# HEALTH
# =========================
@app.get("/")
def root():
    return {"status": "ok", "target": TARGET}

@app.get("/health")
def health():
    return {"status": "healthy"}