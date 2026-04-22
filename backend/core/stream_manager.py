# import cv2

# cap = None
# detect_enabled = False


# def load_video(path):
#     global cap
#     if cap:
#         cap.release()
#     cap = cv2.VideoCapture(path)


# def get_frame():
#     global cap
#     if cap is None:
#         return None, False

#     ret, frame = cap.read()

#     if not ret:
#         cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
#         return None, False

#     return frame, True


# def enable_detect():
#     global detect_enabled
#     detect_enabled = True


# def disable_detect():
#     global detect_enabled
#     detect_enabled = False


# def is_detect_enabled():
#     return detect_enabled