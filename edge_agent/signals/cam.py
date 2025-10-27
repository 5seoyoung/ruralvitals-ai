# edge_agent/signals/cam.py
import cv2
import numpy as np

class CamSource:
    def __init__(self, index=0):
        self.cap = cv2.VideoCapture(index)
        self.prev = None

    def read_motion(self):
        ok, frame = self.cap.read()
        if not ok or frame is None:
            return None, 0.0
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (9,9), 0)
        if self.prev is None:
            self.prev = gray
            return frame, 0.0
        diff = cv2.absdiff(self.prev, gray)
        self.prev = gray
        motion = float(np.mean(diff) / 255.0)
        return frame, motion
