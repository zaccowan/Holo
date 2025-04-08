# Imports for GUI library and styling system
import tkinter.messagebox
import tkinter.ttk

# Imports for hand tracking and mouse manipulation
import math
import cv2

from config import DEFAULT_FRAME_HEIGHT, DEFAULT_FRAME_WIDTH


#################################
# Hand Configuration
#################################


class HandTrackingCalibrationFunctions:
    def __init__(self):
        pass

    def auto_configure_left_bound(self):
        """Set left bound to current palm position"""
        if self.camera_running and hasattr(self, "hands"):
            ret, frame = self.cap.read()
            if ret:
                if hasattr(self, "flip_camera_enabled") and self.flip_camera_enabled:
                    frame = cv2.flip(frame, 1)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.hands.process(frame_rgb)

                if results.multi_hand_landmarks:
                    palm = results.multi_hand_landmarks[0].landmark[
                        self.mp_hands.HandLandmark.WRIST
                    ]
                    x_pos = palm.x * DEFAULT_FRAME_WIDTH
                    self.left_bound_scroller.set(x_pos)

    def auto_configure_right_bound(self):
        """Set right bound to current palm position"""
        if self.camera_running and hasattr(self, "hands"):
            ret, frame = self.cap.read()
            if ret:
                if hasattr(self, "flip_camera_enabled") and self.flip_camera_enabled:
                    frame = cv2.flip(frame, 1)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.hands.process(frame_rgb)

                if results.multi_hand_landmarks:
                    palm = results.multi_hand_landmarks[0].landmark[
                        self.mp_hands.HandLandmark.WRIST
                    ]
                    x_pos = palm.x * DEFAULT_FRAME_WIDTH
                    self.right_bound_scroller.set(x_pos)

    def auto_configure_top_bound(self):
        """Set top bound to current palm position"""
        if self.camera_running and hasattr(self, "hands"):
            ret, frame = self.cap.read()
            if ret:
                if hasattr(self, "flip_camera_enabled") and self.flip_camera_enabled:
                    frame = cv2.flip(frame, 1)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.hands.process(frame_rgb)

                if results.multi_hand_landmarks:
                    palm = results.multi_hand_landmarks[0].landmark[
                        self.mp_hands.HandLandmark.WRIST
                    ]
                    y_pos = palm.y * DEFAULT_FRAME_HEIGHT
                    self.top_bound_scroller.set(y_pos)

    def auto_configure_bottom_bound(self):
        """Set bottom bound to current palm position"""
        if self.camera_running and hasattr(self, "hands"):
            ret, frame = self.cap.read()
            if ret:
                if hasattr(self, "flip_camera_enabled") and self.flip_camera_enabled:
                    frame = cv2.flip(frame, 1)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.hands.process(frame_rgb)

                if results.multi_hand_landmarks:
                    palm = results.multi_hand_landmarks[0].landmark[
                        self.mp_hands.HandLandmark.WRIST
                    ]
                    y_pos = palm.y * DEFAULT_FRAME_HEIGHT
                    self.bottom_bound_scroller.set(y_pos)

    def configure_depth(self):
        """Configure depth calibration based on initial hand position"""
        if not self.camera_running or not hasattr(self, "hands"):
            return

        # Get initial frame and hand position
        ret, frame = self.cap.read()
        if not ret:
            return

        if hasattr(self, "flip_camera_enabled") and self.flip_camera_enabled:
            frame = cv2.flip(frame, 1)

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(frame_rgb)

        if results.multi_hand_landmarks:
            # Get initial hand size as depth reference
            hand_landmarks = results.multi_hand_landmarks[0]

            # Calculate hand size using distance between wrist and middle finger MCP
            wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
            middle_mcp = hand_landmarks.landmark[
                self.mp_hands.HandLandmark.MIDDLE_FINGER_MCP
            ]

            # Calculate initial hand size
            initial_hand_size = math.sqrt(
                (wrist.x - middle_mcp.x) ** 2 + (wrist.y - middle_mcp.y) ** 2
            )

            # Store initial values
            self.depth_reference = {
                "initial_size": initial_hand_size,
                "initial_bounds": {
                    "left": self.left_bound_scroller.get(),
                    "right": self.right_bound_scroller.get(),
                    "top": self.top_bound_scroller.get(),
                    "bottom": self.bottom_bound_scroller.get(),
                },
            }

            # Update depth button to show calibrated state
            self.depth_btn.configure(text="Depth Calibrated", fg_color="green")

            # Start depth tracking in camera loop
            self.depth_tracking = True

    def get_current_depth_ratio(self):
        """Get current depth ratio from hand tracking"""
        try:
            if (
                hasattr(self, "hands")
                and self.camera_running
                and hasattr(self, "depth_reference")
            ):
                ret, frame = self.cap.read()
                if ret:
                    if (
                        hasattr(self, "flip_camera_enabled")
                        and self.flip_camera_enabled
                    ):
                        frame = cv2.flip(frame, 1)
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = self.hands.process(frame_rgb)

                    if results.multi_hand_landmarks:
                        hand_landmarks = results.multi_hand_landmarks[0]
                        wrist = hand_landmarks.landmark[
                            self.mp_hands.HandLandmark.WRIST
                        ]
                        middle_mcp = hand_landmarks.landmark[
                            self.mp_hands.HandLandmark.MIDDLE_FINGER_MCP
                        ]
                        current_hand_size = math.sqrt(
                            (wrist.x - middle_mcp.x) ** 2
                            + (wrist.y - middle_mcp.y) ** 2
                        )
                        return current_hand_size / self.depth_reference["initial_size"]
        except Exception as e:
            print(f"Error getting depth ratio: {e}")
        return 1.0  # Default to no scaling if something goes wrong
