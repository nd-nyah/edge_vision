import cv2
from typing import Optional, Tuple, Literal


class JetsonPipeline:
    def __init__(self, resolution: Tuple[int, int] = (640, 480), fps: int = 30):
        self.resolution = resolution
        self.fps = fps

        self.cap: Optional[cv2.VideoCapture] = None
        self.source: Optional[Literal["gstreamer", "opencv"]] = None

    # ---------------------------------------------------
    # Build GStreamer pipeline (Jetson optimized)
    # ---------------------------------------------------
    def _gstreamer_pipeline(self) -> str:
        width, height = self.resolution
        fps = self.fps

        return (
            "nvarguscamerasrc ! "
            "video/x-raw(memory:NVMM), "
            f"width=(int){width}, height=(int){height}, "
            f"framerate=(fraction){fps}/1 ! "
            "nvvidconv flip-method=0 ! "
            "video/x-raw, width=(int){width}, height=(int){height}, format=(BGRx) ! "
            "videoconvert ! "
            "video/x-raw, format=(BGR) ! appsink"
        )

    # ---------------------------------------------------
    # Initialize camera
    # ---------------------------------------------------
    def init(self) -> bool:
        print(f"[JETSON PIPELINE] Init camera @ {self.resolution}")

        # -------------------------
        # 1. Try GStreamer (BEST)
        # -------------------------
        try:
            pipeline = self._gstreamer_pipeline()

            self.cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)

            if self.cap.isOpened():
                self.source = "gstreamer"
                print("[JETSON PIPELINE] Using GStreamer pipeline ✅")
                return True

        except Exception as e:
            print(f"[JETSON PIPELINE] GStreamer failed: {e}")

        # -------------------------
        # 2. Fallback OpenCV (/dev/video0)
        # -------------------------
        try:
            self.cap = cv2.VideoCapture(0)

            if not self.cap.isOpened():
                raise RuntimeError("OpenCV camera not available")

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])

            self.source = "opencv"

            print("[JETSON PIPELINE] Using OpenCV fallback camera ⚠️")
            return True

        except Exception as e:
            print(f"[JETSON PIPELINE] Camera init failed ❌: {e}")
            return False

    # ---------------------------------------------------
    # Read frame
    # ---------------------------------------------------
    def read(self):
        if self.cap is None:
            return None

        ret, frame = self.cap.read()

        if not ret:
            return None

        return frame

    # ---------------------------------------------------
    # Cleanup
    # ---------------------------------------------------
    def release(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None