import cv2
import numpy as np
import onnxruntime as ort

class Detector:
    def __init__(self, model_path="yolov5s.onnx"):
        self.session = ort.InferenceSession(
            model_path,
            providers=["CPUExecutionProvider"]
        )

        self.input_name = self.session.get_inputs()[0].name

        self.conf_threshold = 0.45
        self.iou_threshold = 0.45

        # COCO class names (same as YOLOv5)
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

    def preprocess(self, frame):
        img = cv2.resize(frame, (640, 640))
        img = img[:, :, ::-1]  # BGR → RGB
        img = img.transpose(2, 0, 1)  # HWC → CHW
        img = np.expand_dims(img, axis=0)
        img = img.astype(np.float32) / 255.0
        return img

    def predict(self, frame):
        if frame is None:
            return []

        input_tensor = self.preprocess(frame)

        outputs = self.session.run(None, {self.input_name: input_tensor})
        preds = outputs[0]  # shape: (1, N, 85)

        detections = []

        for det in preds[0]:
            conf = det[4]

            if conf < self.conf_threshold:
                continue

            class_scores = det[5:]
            cls = np.argmax(class_scores)
            score = class_scores[cls] * conf

            if score < self.conf_threshold:
                continue

            cx, cy, w, h = det[:4]

            # convert to xyxy
            x1 = int(cx - w / 2)
            y1 = int(cy - h / 2)
            x2 = int(cx + w / 2)
            y2 = int(cy + h / 2)

            detections.append({
                "label": self.names[int(cls)],
                "confidence": float(score),
                "bbox": {
                    "x": x1,
                    "y": y1,
                    "w": int(w),
                    "h": int(h)
                }
            })

        return detections