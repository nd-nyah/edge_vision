# from fastapi import APIRouter, WebSocket
# import asyncio
# import cv2
# import base64

# from core.stream_manager import (
#     get_frame,
#     enable_detect,
#     disable_detect,
#     is_detect_enabled,
# )
# from services.detector_service import run_detection

# router = APIRouter()


# def encode_frame(frame):
#     _, buffer = cv2.imencode(".jpg", frame)
#     return base64.b64encode(buffer).decode("utf-8")


# @router.post("/start-detect")
# async def start_detect():
#     enable_detect()
#     return {"status": "detect ON"}


# @router.post("/stop-detect")
# async def stop_detect():
#     disable_detect()
#     return {"status": "detect OFF"}


# @router.websocket("/ws/stream")
# async def stream(ws: WebSocket):
#     await ws.accept()

#     try:
#         while True:
#             frame, ok = get_frame()

#             if not ok:
#                 await ws.send_json({
#                     "frame": None,
#                     "detections": [],
#                     "status": "no video"
#                 })
#                 await asyncio.sleep(0.1)
#                 continue

#             frame = cv2.resize(frame, (640, 360))

#             if is_detect_enabled():
#                 detections = run_detection(frame)
#                 status = "detecting"
#             else:
#                 detections = []
#                 status = "ready"

#             await ws.send_json({
#                 "frame": encode_frame(frame),
#                 "detections": detections,
#                 "status": status
#             })

#             await asyncio.sleep(0.03)

#     except Exception as e:
#         print("WS error:", e)