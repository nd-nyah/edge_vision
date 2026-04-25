import cv2
import numpy as np
import onnxruntime as ort


class Detector:
    def __init__(self, model_path):
        # print("🔥 Detector initialized")
        self.session = ort.InferenceSession(
            model_path,
            providers=["CPUExecutionProvider"]
        )

        self.input_name = self.session.get_inputs()[0].name
        self.conf_threshold = 0.45

        # COCO classes
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
    # PREPROCESS
    # =========================
    def preprocess(self, frame):
        img = cv2.resize(frame, (640, 640))
        img = img[:, :, ::-1]  # BGR → RGB
        img = img.transpose(2, 0, 1)  # HWC → CHW
        img = np.expand_dims(img, axis=0)
        img = img.astype(np.float32) / 255.0
        return img

    # =========================
    # PREDICT
    # =========================
    def predict(self, frame):
        if frame is None:
            return []

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

            class_scores = det[5:]
            cls = np.argmax(class_scores)
            cls_conf = class_scores[cls]

            score = obj_conf * cls_conf

            if score < self.conf_threshold:
                continue

            cx, cy, w, h = det[:4]

            x1 = cx - w / 2
            y1 = cy - h / 2

            detections.append({
                "label": self.names[int(cls)],
                "confidence": float(score),
                "bbox": {
                    "x": float(x1),
                    "y": float(y1),
                    "w": float(w),
                    "h": float(h)
                }
            })

        return detections

    # =========================
    # DRAW BOXES
    # =========================
    def draw(self, frame, detections):
        h, w, _ = frame.shape

        for det in detections:
            x = det["bbox"]["x"]
            y = det["bbox"]["y"]
            bw = det["bbox"]["w"]
            bh = det["bbox"]["h"]

            label = det["label"]
            conf = det["confidence"]

            # scale to original frame
            x = int(x * w / 640)
            y = int(y * h / 640)
            bw = int(bw * w / 640)
            bh = int(bh * h / 640)

            # clamp
            x = max(0, x)
            y = max(0, y)
            bw = max(0, bw)
            bh = max(0, bh)

            x2 = min(w, x + bw)
            y2 = min(h, y + bh)

            cv2.rectangle(frame, (x, y), (x2, y2), (0, 255, 0), 2)

            cv2.putText(
                frame,
                f"{label} {conf:.2f}",
                (x, max(20, y - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2
            )

        return frame

    # =========================
    # PIPELINE
    # =========================
    def detect(self, frame):
        detections = self.predict(frame)
        drawn_frame = self.draw(frame.copy(), detections)
        return detections, drawn_frame