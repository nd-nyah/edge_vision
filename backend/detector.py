import cv2
import numpy as np
import onnxruntime as ort
from ultralytics import YOLO


class Detector:
    def __init__(self, yolov5_path, yoloworld_path):

        self.conf_threshold = 0.25
        self.text_prompts = []

        # =========================
        # YOLOv5 (ONNX)
        # =========================
        self.session = ort.InferenceSession(
            yolov5_path,
            providers=["CPUExecutionProvider"]
        )
        self.input_name = self.session.get_inputs()[0].name

        self.names = [
            "person","bicycle","car","motorcycle","airplane","bus","train","truck","boat",
            "traffic light","fire hydrant","stop sign","parking meter","bench","bird","cat",
            "dog","horse","sheep","cow","elephant","bear","zebra","giraffe","backpack","umbrella",
            "handbag","tie","suitcase","frisbee","skis","snowboard","sports ball","kite","baseball bat",
            "baseball glove","skateboard","surfboard","tennis racket","bottle","wine glass","cup",
            "fork","knife","spoon","bowl","banana","apple","sandwich","orange","broccoli","carrot",
            "hot dog","pizza","donut","cake","chair","couch","potted plant","bed","dining table",
            "toilet","tv","laptop","mouse","remote","keyboard","cell phone","microwave","oven",
            "toaster","sink","refrigerator","book","clock","vase","scissors","teddy bear","hair drier",
            "toothbrush"
        ]

        # =========================
        # YOLO-World
        # =========================
        self.world_model = YOLO(yoloworld_path)

    # =========================
    # PROMPTS
    # =========================
    def set_prompts(self, prompts):
        self.text_prompts = prompts or []

    # =========================
    # PREPROCESS YOLOv5
    # =========================
    def preprocess(self, frame):
        img = cv2.resize(frame, (640, 640))
        img = img[:, :, ::-1]
        img = img.transpose(2, 0, 1)
        img = np.expand_dims(img, axis=0)
        return img.astype(np.float32) / 255.0

    # =========================
    # AUTO SWITCH PREDICT
    # =========================
    def predict(self, frame):
        if frame is None:
            return []

        # 🔥 AUTO SWITCH LOGIC
        if self.text_prompts:
            return self._predict_yoloworld(frame)
        else:
            return self._predict_yolov5(frame)

    # =========================
    # YOLOv5
    # =========================
    def _predict_yolov5(self, frame):
        h0, w0 = frame.shape[:2]

        input_tensor = self.preprocess(frame)
        outputs = self.session.run(None, {self.input_name: input_tensor})
        preds = np.squeeze(outputs[0])

        detections = []

        for det in preds:
            if len(det) < 6:
                continue

            obj_conf = det[4]
            if obj_conf < self.conf_threshold:
                continue

            cls_scores = det[5:]
            cls = int(np.argmax(cls_scores))
            score = obj_conf * cls_scores[cls]

            if score < self.conf_threshold:
                continue

            cx, cy, w, h = det[:4]

            x_scale = w0 / 640
            y_scale = h0 / 640

            x1 = (cx - w / 2) * x_scale
            y1 = (cy - h / 2) * y_scale

            detections.append({
                "label": self.names[cls],
                "confidence": float(score),
                "bbox": {
                    "x": float(x1),
                    "y": float(y1),
                    "w": float(w * x_scale),
                    "h": float(h * y_scale)
                }
            })

        return detections

    # =========================
    # YOLO-WORLD
    # =========================
    def _predict_yoloworld(self, frame):

        if self.text_prompts:
            try:
                self.world_model.set_classes(self.text_prompts)
            except Exception:
                pass

        results = self.world_model.predict(
            source=frame,
            conf=self.conf_threshold,
            verbose=False
        )

        detections = []

        for r in results:
            if r.boxes is None:
                continue

            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])

                label = (
                    self.text_prompts[cls_id]
                    if self.text_prompts and cls_id < len(self.text_prompts)
                    else "object"
                )

                detections.append({
                    "label": label,
                    "confidence": conf,
                    "bbox": {
                        "x": x1,
                        "y": y1,
                        "w": x2 - x1,
                        "h": y2 - y1
                    }
                })

        return detections

    # =========================
    # DRAW
    # =========================
    def draw(self, frame, detections):
        for d in detections:
            x = int(d["bbox"]["x"])
            y = int(d["bbox"]["y"])
            w = int(d["bbox"]["w"])
            h = int(d["bbox"]["h"])

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            cv2.putText(
                frame,
                f"{d['label']} {d['confidence']:.2f}",
                (x, max(20, y - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2
            )

        return frame

    def detect(self, frame):
        detections = self.predict(frame)
        drawn = self.draw(frame.copy(), detections)
        return detections, drawn
