# from fastapi import APIRouter, Depends
# from fastapi.responses import StreamingResponse
# import json
# import time

# from picamera2 import Picamera2
# from backend.config import get_detector

# router = APIRouter()


# @router.get("/stream")
# def stream(detector=Depends(get_detector)):

#     picam2 = Picamera2()
#     picam2.configure(picam2.create_video_configuration())
#     picam2.start()

#     def generate():
#         while True:
#             frame = picam2.capture_array()

#             if frame is None:
#                 continue

#             results = detector.predict(frame)

#             yield json.dumps({
#                 "type": "stream",
#                 "results": results
#             }) + "\n"

#             time.sleep(0.1)

#     return StreamingResponse(generate(), media_type="text/plain")