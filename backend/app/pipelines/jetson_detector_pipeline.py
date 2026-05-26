import cv2
import time
import os
from collections import deque

from app.services.agents.adaptive_bc_agent import ComputeAgent, FPSState


class JetsonDetectorPipeline:

    def __init__(self, detector, time_window=0.5):

        self.detector = detector
        self.agent = ComputeAgent()

        # 🔥 HOST CAMERA STREAM (NO CSI)
        self.camera_url = os.getenv(
            "CAMERA_URL",
            "http://127.0.0.1:9000/video"
        )

        self.TIME_WINDOW = time_window

        self.base_memory = deque(maxlen=300)
        self.agent_memory = deque(maxlen=300)

        self.fps_counter = 0
        self.fps_timer = time.time()
        self.current_fps = 0

        self.base_latency = 0
        self.agent_latency = 0

        self.latest_output = None
        self.running = False

    # =========================
    # FPS
    # =========================
    def update_fps(self):
        self.fps_counter += 1
        elapsed = time.time() - self.fps_timer

        if elapsed >= 1.0:
            self.current_fps = self.fps_counter / elapsed
            self.fps_counter = 0
            self.fps_timer = time.time()

    # =========================
    # DETECTION
    # =========================
    def _detect(self, frame, memory, now):

        rgb = frame[:, :, ::-1]

        detections, _ = self.detector.detect(rgb)
        detections = detections or []

        for d in detections:
            memory.append({
                "data": d,
                "time": now
            })

        return [
            x["data"]
            for x in memory
            if now - x["time"] < self.TIME_WINDOW
        ]

    # =========================
    # MAIN PROCESS
    # =========================
    def process_frame(self, frame):

        self.update_fps()
        now = time.time()

        # BASELINE
        base = frame.copy()
        t0 = time.time()

        base_vis = self._detect(base, self.base_memory, now)
        base_draw = self.detector.draw(base, base_vis)

        self.base_latency = (time.time() - t0) * 1000

        # AGENT
        state = FPSState(
            fps=self.current_fps,
            object_count=len(base_vis)
        )

        action = self.agent.decide(state)

        agent = frame.copy()
        t1 = time.time()

        if action.mode == "LOW_POWER":
            run = (self.fps_counter % 2 == 0)
        elif action.mode == "ULTRA_LOW_POWER":
            run = (self.fps_counter % 4 == 0)
        else:
            run = True

        if run:
            agent_vis = self._detect(agent, self.agent_memory, now)
        else:
            agent_vis = [
                x["data"]
                for x in self.agent_memory
                if now - x["time"] < self.TIME_WINDOW
            ]

        agent_draw = self.detector.draw(agent, agent_vis)

        self.agent_latency = (time.time() - t1) * 1000

        return {
            "frame": agent_draw,
            "detections": agent_vis,
            "fps": round(self.current_fps, 2),

            "baseline": {
                "frame": base_draw,
                "latency_ms": round(self.base_latency, 2),
            },

            "agent": {
                "frame": agent_draw,
                "latency_ms": round(self.agent_latency, 2),
                "mode": action.mode,
            },

            "metrics": {
                "baseline_latency_ms": round(self.base_latency, 2),
                "agent_latency_ms": round(self.agent_latency, 2),
            }
        }

    # =========================
    # CAMERA LOOP (HOST STREAM)
    # =========================
    def camera_loop(self):

        print(f"[CAM] Connecting to {self.camera_url}")

        cap = cv2.VideoCapture(self.camera_url)

        if not cap.isOpened():
            raise RuntimeError("Failed to open host camera stream")

        self.running = True

        while self.running:

            ret, frame = cap.read()
            if not ret:
                continue

            self.latest_output = self.process_frame(frame)

        cap.release()

    # =========================
    # START
    # =========================
    def start(self):

        if self.running:
            return

        import threading

        threading.Thread(
            target=self.camera_loop,
            daemon=True
        ).start()

        print("[PIPELINE] Started (HOST CAMERA MODE)")

    # =========================
    # OUTPUT
    # =========================
    def get_latest_output(self):
        return self.latest_output

    def get_jpeg(self):

        if not self.latest_output:
            return None

        frame = self.latest_output["frame"]

        ok, buf = cv2.imencode(
            ".jpg",
            frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), 70]
        )

        if not ok:
            return None

        return buf.tobytes()
