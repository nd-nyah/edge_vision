import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from upload_video import router as upload_router
from video_stream import router as video_router
# from prompt_stream import router as prompt_router

app = FastAPI()

# =========================
# BASE PATH
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_DIR = os.path.join(BASE_DIR, "video")

os.makedirs(VIDEO_DIR, exist_ok=True)

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
# ROUTES
# =========================
app.include_router(upload_router, prefix="/api")
app.include_router(video_router, prefix="/api")
# app.include_router(prompt_router)

# =========================
# STATIC FILES (optional)
# =========================
app.mount(
    "/videos",
    StaticFiles(directory=VIDEO_DIR),
    name="videos"
)

# =========================
# ROOT
# =========================
@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "YOLO Video Stream API running"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}