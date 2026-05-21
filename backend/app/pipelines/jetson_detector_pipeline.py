import cv2
import time
import threading
from collections import deque

from app.services.agents.adaptive_bc_agent import (
    ComputeAgent,
    FPSState,
)


class JetsonDetectorPipeline:

    def __init__(
        self,
        detector,
        sensor_id=0,
        width=1280,
        height=720,
        fps=30,
        time_window=0.5,
    ):

        self.detector = detector
        self.agent = ComputeAgent()

        self.sensor_id = sensor_id
        self.width = width
        self.height = height
        self.camera_fps = fps

        self.TIME_WINDOW = time_window

        # ==========================================
        # MEMORY
        # ==========================================
        self.base_memory = deque(maxlen=300)
        self.agent_memory = deque(maxlen=300)

        # ==========================================
        # FPS
        # ==========================================
        self.fps_counter = 0
        self.fps_timer = time.time()
        self.current_fps = 0

        # ==========================================
        # LATENCY
        # ==========================================
        self.base_latency = 0
        self.agent_latency = 0

        # ==========================================
        # SHARED OUTPUT
        # ==========================================
        self.latest_output = None
        self.output_lock = threading.Lock()

        # ==========================================
        # THREAD CONTROL
        # ==========================================
        self.running = False

    # =====================================================
    # GSTREAMER
    # =====================================================
    def gstreamer_pipeline(self):

        return (
            f"nvarguscamerasrc sensor-id={self.sensor_id} ! "
            f"video/x-raw(memory:NVMM), "
            f"width=(int){self.width}, "
            f"height=(int){self.height}, "
            f"framerate=(fraction){self.camera_fps}/1 ! "
            "nvvidconv flip-method=0 ! "
            "video/x-raw, format=(string)BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=(string)BGR ! "
            "appsink drop=true max-buffers=1 sync=false"
        )

    # =====================================================
    # FPS
    # =====================================================
    def update_fps(self):

        self.fps_counter += 1

        elapsed = time.time() - self.fps_timer

        if elapsed >= 1.0:

            self.current_fps = self.fps_counter / elapsed

            self.fps_counter = 0
            self.fps_timer = time.time()

    # =====================================================
    # OBJECT ID
    # =====================================================
    def make_id(self, detection):

        x = int(detection["bbox"]["x"] // 30)
        y = int(detection["bbox"]["y"] // 30)

        return f"{detection['label']}_{x}_{y}"

    # =====================================================
    # DETECT
    # =====================================================
    def _detect(self, frame, memory, now):

        rgb_frame = frame[:, :, ::-1]

        detections, _ = self.detector.detect(rgb_frame)

        if not detections:
            detections = []

        for d in detections:

            memory.append({
                "id": self.make_id(d),
                "data": d,
                "time": now
            })

        visible = [
            x["data"]
            for x in memory
            if now - x["time"] < self.TIME_WINDOW
        ]

        return visible

    # =====================================================
    # MAIN PIPELINE
    # =====================================================
    def process_frame(self, frame):

        self.update_fps()

        now = time.time()

        # =================================================
        # 🔴 BASELINE
        # =================================================
        base_frame = frame.copy()

        base_start = time.time()

        base_visible = self._detect(
            base_frame,
            self.base_memory,
            now
        )

        base_drawn = self.detector.draw(
            base_frame,
            base_visible
        )

        self.base_latency = (
            time.time() - base_start
        ) * 1000

        # =================================================
        # 🟢 AGENT
        # =================================================
        object_count = len(base_visible)

        state = FPSState(
            fps=self.current_fps,
            object_count=object_count
        )

        action = self.agent.decide(state)

        agent_frame = frame.copy()

        agent_start = time.time()

        run_detection = True

        # ==============================================
        # AGENT CONTROL
        # ==============================================
        if action.mode == "LOW_POWER":

            run_detection = (
                self.fps_counter % 2 == 0
            )

        elif action.mode == "ULTRA_LOW_POWER":

            run_detection = (
                self.fps_counter % 4 == 0
            )

        # ==============================================
        # DETECT OR REUSE MEMORY
        # ==============================================
        if run_detection:

            agent_visible = self._detect(
                agent_frame,
                self.agent_memory,
                now
            )

        else:

            agent_visible = [
                x["data"]
                for x in self.agent_memory
                if now - x["time"] < self.TIME_WINDOW
            ]

        agent_drawn = self.detector.draw(
            agent_frame,
            agent_visible
        )

        self.agent_latency = (
            time.time() - agent_start
        ) * 1000

        # =================================================
        # METRICS
        # =================================================
        load_ratio = self.agent_latency / max(
            self.base_latency,
            1e-6
        )

        return {
            "frame": agent_drawn,
            "detections": agent_visible,
            "fps": round(self.current_fps, 2),
            "mode": action.mode,

            "baseline": {
                "frame": base_drawn,
                "detections": base_visible,
                "latency_ms": round(
                    self.base_latency,
                    2
                ),
            },

            "agent": {
                "frame": agent_drawn,
                "detections": agent_visible,
                "latency_ms": round(
                    self.agent_latency,
                    2
                ),
                "mode": action.mode
            },

            "metrics": {
                "baseline_latency_ms":
                    round(self.base_latency, 2),

                "agent_latency_ms":
                    round(self.agent_latency, 2),

                "load_ratio":
                    round(load_ratio, 2),
            }
        }

    # =====================================================
    # CAMERA LOOP
    # =====================================================
    def camera_loop(self):

        cap = cv2.VideoCapture(
            self.gstreamer_pipeline(),
            cv2.CAP_GSTREAMER
        )

        if not cap.isOpened():
            raise RuntimeError(
                "Failed to open CSI camera"
            )

        # Camera warmup
        for _ in range(10):
            cap.read()

        print("[JETSON] Camera started")

        while self.running:

            ret, frame = cap.read()

            if not ret:
                continue

            output = self.process_frame(frame)

            with self.output_lock:
                self.latest_output = output

        cap.release()

    # =====================================================
    # START
    # =====================================================
    def start(self):

        if self.running:
            return

        self.running = True

        self.worker = threading.Thread(
            target=self.camera_loop,
            daemon=True
        )

        self.worker.start()

        print("[JETSON] Pipeline started")

    # =====================================================
    # STOP
    # =====================================================
    def stop(self):

        self.running = False

    # =====================================================
    # OUTPUT
    # =====================================================
    def get_latest_output(self):

        with self.output_lock:

            return self.latest_output

    # =====================================================
    # JPEG
    # =====================================================
    def get_jpeg(self):

        with self.output_lock:

            if self.latest_output is None:
                return None

            frame = self.latest_output["frame"]

        success, buffer = cv2.imencode(
            ".jpg",
            frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), 70]
        )

        if not success:
            return None

        return buffer.tobytes()