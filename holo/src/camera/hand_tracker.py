import cv2
import mediapipe as mp
import numpy as np
from ..config.settings import HandTrackingSettings


class HandTracker:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=HandTrackingSettings.MAX_NUM_HANDS,
            min_detection_confidence=HandTrackingSettings.MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=HandTrackingSettings.MIN_TRACKING_CONFIDENCE,
        )

    def process_frame(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        return results

    def draw_landmarks(self, frame, results):
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style(),
                )

    def get_hand_position(self, results, frame_width, frame_height):
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Index finger tip coordinates
                x = hand_landmarks.landmark[8].x * frame_width
                y = hand_landmarks.landmark[8].y * frame_height
                return x, y
        return None
