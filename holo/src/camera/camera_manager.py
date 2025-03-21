import cv2
import threading
import numpy as np
from ..config.settings import CameraSettings
from .hand_tracker import HandTracker


class CameraManager:
    def __init__(self):
        self.cap = None
        self.camera_running = False
        self.stop_event = threading.Event()
        self.frame_width = CameraSettings.FRAME_WIDTH
        self.frame_height = CameraSettings.FRAME_HEIGHT
        self.hand_tracker = HandTracker()
        self.flip_enabled = False

    def list_available_cameras(self):
        available_ports = []
        for i in range(4):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    available_ports.append(i)
                cap.release()
        return available_ports

    def open_camera(self, camera_index):
        if not self.camera_running:
            self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)

            if not self.cap.isOpened():
                raise RuntimeError(f"Failed to open camera {camera_index}")

            self.camera_running = True
            self.stop_event.clear()
            return True
        return False

    def close_camera(self):
        self.camera_running = False
        self.stop_event.set()
        if self.cap:
            self.cap.release()
            self.cap = None
        cv2.destroyAllWindows()

    def read_frame(self):
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret and self.flip_enabled:
                frame = cv2.flip(frame, 1)
            return ret, frame
        return False, None
