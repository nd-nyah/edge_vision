import cv2

cap = cv2.VideoCapture("/mnt/e/12207144_1920_1080_30fps.mp4")

print("OPEN:", cap.isOpened())

while True:
    ret, frame = cap.read()

    print("FRAME:", ret)

    if not ret:
        break