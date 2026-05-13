import time
import cv2
from typing import Optional, Literal, Tuple

try:
    from picamera2 import Picamera2
    PICAMERA_AVAILABLE = True
except Exception:
    PICAMERA_AVAILABLE = False


class PiPipeline:
    def __init__(
        self,
        resolution: Tuple[int, int] = (640, 480)
    ):
        self.resolution = resolution  # (width, height)

        self.picam2: Optional[Picamera2] = None
        self.cv_cam: Optional[cv2.VideoCapture] = None
        self.source: Optional[Literal["picamera2", "opencv"]] = None

    # ---------------------------------------------------
    # Camera initialization
    # ---------------------------------------------------
    def init(self) -> bool:
        print(f"[PI PIPELINE] Initializing camera @ {self.resolution}...")

        width, height = self.resolution

        # -------------------------
        # 1. PiCamera2 (preferred)
        # -------------------------
        if PICAMERA_AVAILABLE:
            try:
                self.picam2 = Picamera2()

                config = self.picam2.create_video_configuration(
                    main={
                        "size": (width, height),
                        "format": "RGB888"
                    }
                )

                self.picam2.configure(config)
                self.picam2.start()

                time.sleep(1)

                self.source = "picamera2"

                print(f"[PI PIPELINE] Using Picamera2 @ {width}x{height} ✅")
                return True

            except Exception as e:
                print(f"[PI PIPELINE] Picamera2 failed: {e}")

        # -------------------------
        # 2. Fallback OpenCV
        # -------------------------
        try:
            self.cv_cam = cv2.VideoCapture(0)

            if not self.cv_cam.isOpened():
                raise RuntimeError("OpenCV camera not available")

            # Try to set resolution (may or may not be honored)
            self.cv_cam.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cv_cam.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

            self.source = "opencv"

            print(f"[PI PIPELINE] Using OpenCV camera @ {width}x{height} ✅")
            return True

        except Exception as e:
            print(f"[PI PIPELINE] No camera available ❌: {e}")
            return False

    # ---------------------------------------------------
    # Unified frame reader
    # ---------------------------------------------------
    def read(self):
        if self.source == "picamera2" and self.picam2 is not None:
            return self.picam2.capture_array()

        if self.source == "opencv" and self.cv_cam is not None:
            ret, frame = self.cv_cam.read()
            if not ret:
                return None
            return frame

        return None

    # ---------------------------------------------------
    # Cleanup
    # ---------------------------------------------------
    def release(self):
        if self.picam2 is not None:
            try:
                self.picam2.stop()
            except Exception:
                pass

        if self.cv_cam is not None:
            self.cv_cam.release()