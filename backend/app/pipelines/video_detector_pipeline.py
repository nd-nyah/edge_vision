import time
from collections import deque

from app.services.agents.adaptive_bc_agent import ComputeAgent, FPSState


class DetectorPipeline:

    def __init__(self, detector, time_window=0.5):
        self.detector = detector
        self.agent = ComputeAgent()
        self.TIME_WINDOW = time_window

        self.base_memory = deque(maxlen=300)
        self.agent_memory = deque(maxlen=300)

        self.fps_counter = 0
        self.fps_timer = time.time()
        self.current_fps = 0

        # -------------------------
        # LATENCY TRACKING
        # -------------------------
        self.base_latency = 0
        self.agent_latency = 0

    # -------------------------
    # FPS tracking
    # -------------------------
    def update_fps(self):
        self.fps_counter += 1
        elapsed = time.time() - self.fps_timer

        if elapsed >= 1.0:
            self.current_fps = self.fps_counter / elapsed
            self.fps_counter = 0
            self.fps_timer = time.time()

    # -------------------------
    # ID generator
    # -------------------------
    def make_id(self, detection):
        x = int(detection["bbox"]["x"] // 30)
        y = int(detection["bbox"]["y"] // 30)
        return f"{detection['label']}_{x}_{y}"

    # -------------------------
    # DETECTION
    # -------------------------
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

        return detections

    # -------------------------
    # MAIN PIPELINE (A/B VERSION)
    # -------------------------
    def process_frame(self, frame, frame_idx):

        self.update_fps()
        now = time.time()

        # =================================================
        # 🔴 BASELINE PIPELINE (REAL)
        # =================================================
        base_frame = frame.copy()

        base_start = time.time()

        base_detections = self._detect(
            base_frame,
            self.base_memory,
            now
        )

        base_visible = [
            x["data"]
            for x in self.base_memory
            if now - x["time"] < self.TIME_WINDOW
        ]

        base_drawn = self.detector.draw(base_frame, base_visible)

        self.base_latency = (time.time() - base_start) * 1000

        # =================================================
        # 🟢 AGENT PIPELINE (REAL)
        # =================================================
        agent_frame = frame.copy()

        object_count = len([
            x for x in self.base_memory
            if now - x["time"] < self.TIME_WINDOW
        ])

        state = FPSState(
            fps=self.current_fps,
            object_count=object_count
        )

        action = self.agent.decide(state)

        agent_start = time.time()

        agent_detections = self._detect(
            agent_frame,
            self.agent_memory,
            now
        )

        agent_visible = [
            x["data"]
            for x in self.agent_memory
            if now - x["time"] < self.TIME_WINDOW
        ]

        agent_drawn = self.detector.draw(agent_frame, agent_visible)

        self.agent_latency = (time.time() - agent_start) * 1000

        # =================================================
        # 📊 LOAD COMPARISON
        # =================================================
        load_ratio = self.agent_latency / max(self.base_latency, 1e-6)

        # =================================================
        # 🎯 OUTPUT
        # =================================================
        return {
            "frame": agent_drawn,
            "detections": agent_visible,
            "fps": round(self.current_fps, 2),
            "mode": action.mode,
            "batch_size": action.batch_size,

            "baseline": {
                "frame": base_drawn,
                "detections": base_visible,
                "latency_ms": round(self.base_latency, 2),
                "object_count": len(base_visible),
                "fps": round(self.current_fps, 2),
                "mode": "STATIC"
            },

            "agent": {
                "frame": agent_drawn,
                "detections": agent_visible,
                "latency_ms": round(self.agent_latency, 2),
                "object_count": object_count,
                "mode": action.mode
            },

            "metrics": {
                "baseline_latency_ms": round(self.base_latency, 2),
                "agent_latency_ms": round(self.agent_latency, 2),
                "load_ratio": round(load_ratio, 2)
            }
        }