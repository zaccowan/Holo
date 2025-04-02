import threading
import cv2
import time
import math
import numpy as np
from PIL import Image
import customtkinter
import pyautogui

################################
# Webcam Functions
################################


def list_available_cameras(self_instance):
    available_ports = []
    for i in range(4):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                available_ports.append(i)
            cap.release()
    return available_ports


def change_camera(self_instance, selection):
    if self_instance.camera_running:
        self_instance.close_camera()
    camera_index = int(selection.replace("Camera ", ""))
    self_instance.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    self_instance.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self_instance.frame_width)
    self_instance.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self_instance.frame_height)


def toggle_camera_flip(self_instance):
    self_instance.flip_camera_enabled = self_instance.flip_camera.get()


def open_camera(self_instance):
    self_instance.apply_win_style("acrylic")
    if not self_instance.camera_running:
        if self_instance.cap is None or not self_instance.cap.isOpened():
            # Try to open the currently selected camera
            selected_camera = self_instance.camera_select.get()
            camera_index = int(selected_camera.replace("Camera ", ""))
            self_instance.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
            self_instance.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self_instance.frame_width)
            self_instance.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self_instance.frame_height)

            if not self_instance.cap.isOpened():
                print(f"Failed to open camera {camera_index}")
                return

        self_instance.camera_running = True
        self_instance.stop_event.clear()
        self_instance.camera_thread = threading.Thread(target=self_instance.camera_loop)
        self_instance.camera_thread.start()
        self_instance.open_camera_btn.configure(state="disabled")
        self_instance.close_camera_btn.configure(state="normal")
        self_instance.webcam_image_label.configure(text="")


def camera_loop(self_instance):
    mouse_pressed = False
    process_this_frame = True  # Add frame skip counter

    while (
        self_instance.camera_running
        and self_instance.cap is not None
        and self_instance.cap.isOpened()
        and not self_instance.stop_event.is_set()
    ):
        start_time = time.time()
        ret, frame = self_instance.cap.read()
        if not ret:
            break

        # Process every other frame
        if process_this_frame:
            # Resize frame for faster processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)

            if (
                hasattr(self_instance, "flip_camera_enabled")
                and self_instance.flip_camera_enabled
            ):
                small_frame = cv2.flip(small_frame, 1)

            # Convert and process
            opencv_image = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            results = self_instance.hands.process(opencv_image)

            # Scale back up for display
            opencv_image = cv2.resize(
                opencv_image, (self_instance.frame_width, self_instance.frame_height)
            )
        else:
            # Just flip if needed without processing
            if (
                hasattr(self_instance, "flip_camera_enabled")
                and self_instance.flip_camera_enabled
            ):
                frame = cv2.flip(frame, 1)
            opencv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        process_this_frame = not process_this_frame  # Toggle frame processing
        current_click = False

        # Get bounds
        left_bound = self_instance.left_bound_scroller.get()
        right_bound = self_instance.right_bound_scroller.get()
        top_bound = self_instance.top_bound_scroller.get()
        bottom_bound = self_instance.bottom_bound_scroller.get()

        # Draw bounding box
        opencv_image = cv2.rectangle(
            opencv_image,
            (int(left_bound), int(top_bound)),
            (int(right_bound), int(bottom_bound)),
            (255, 255, 255),
            5,
        )

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            index_tip_landmark = hand_landmarks.landmark[
                self_instance.mp_hands.HandLandmark.INDEX_FINGER_TIP
            ]
            thumb_tip_landmark = hand_landmarks.landmark[
                self_instance.mp_hands.HandLandmark.THUMB_TIP
            ]
            palm_landmark = hand_landmarks.landmark[
                self_instance.mp_hands.HandLandmark.WRIST
            ]
            finger_distance = math.hypot(
                index_tip_landmark.x - thumb_tip_landmark.x,
                index_tip_landmark.y - thumb_tip_landmark.y,
            )
            cv2.putText(
                opencv_image,
                "finger_distance: " + str(finger_distance)[:6],
                (30, 50),
                1,
                2,
                (255, 255, 100),
                2,
            )

            if finger_distance < 0.05:  # Threshold for "OK" gesture
                current_click = True

            # Calculate raw mouse position
            mouse_x = np.interp(
                palm_landmark.x * self_instance.frame_width,
                [left_bound, right_bound],
                [0, self_instance.screen_width - 1],
            )
            mouse_y = np.interp(
                palm_landmark.y * self_instance.frame_height,
                [top_bound, bottom_bound],
                [0, self_instance.screen_height - 1],
            )

            # Calculate separate X and Y velocities
            dx = mouse_x - self_instance.previous_mouse_pos[0]
            dy = mouse_y - self_instance.previous_mouse_pos[1]

            # Get bound sizes
            bound_width = right_bound - left_bound
            bound_height = bottom_bound - top_bound

            # Calculate scaling factors based on bound sizes
            width_scale = min(1.0, bound_width / self_instance.min_bound_size)
            height_scale = min(1.0, bound_height / self_instance.min_bound_size)

            # Check if mouse is over canvas
            canvas_rect = (
                self_instance.canvas.winfo_rootx(),
                self_instance.canvas.winfo_rooty(),
                self_instance.canvas.winfo_rootx() + self_instance.canvas.winfo_width(),
                self_instance.canvas.winfo_rooty()
                + self_instance.canvas.winfo_height(),
            )

            is_over_canvas = (
                canvas_rect[0] <= mouse_x <= canvas_rect[2]
                and canvas_rect[1] <= mouse_y <= canvas_rect[3]
            )

            # Calculate adjusted slow factors with extra slowdown when over canvas
            canvas_slowdown = 3.0 if is_over_canvas and finger_distance < 0.05 else 1.0
            x_slow_factor = (
                self_instance.base_slow_factor * width_scale / canvas_slowdown
            )
            y_slow_factor = (
                self_instance.base_slow_factor * height_scale / 2 / canvas_slowdown
            )

            # Apply separate velocity smoothing for X and Y
            if abs(dx) < self_instance.velocity_threshold_x:
                mouse_x = self_instance.previous_mouse_pos[0] + dx * x_slow_factor

            if abs(dy) < self_instance.velocity_threshold_y:
                mouse_y = self_instance.previous_mouse_pos[1] + dy * y_slow_factor

            # Update position history
            self_instance.previous_mouse_pos = (mouse_x, mouse_y)

            # Add to smoothing deque
            self_instance.mouse_x_positions.append(mouse_x)
            self_instance.mouse_y_positions.append(mouse_y)

            # Calculate smoothed position
            smoothed_mouse_x = sum(self_instance.mouse_x_positions) / len(
                self_instance.mouse_x_positions
            )
            smoothed_mouse_y = sum(self_instance.mouse_y_positions) / len(
                self_instance.mouse_y_positions
            )

            if (
                hasattr(self_instance, "mouse_control_enabled")
                and self_instance.mouse_control_enabled
            ):
                pyautogui.moveTo(int(smoothed_mouse_x), int(smoothed_mouse_y))

            self_instance.mp_drawing.draw_landmarks(
                opencv_image, hand_landmarks, self_instance.mp_hands.HAND_CONNECTIONS
            )

            # Add depth tracking logic
            if (
                hasattr(self_instance, "depth_tracking")
                and self_instance.depth_tracking
            ):
                # Calculate current hand size
                wrist = hand_landmarks.landmark[
                    self_instance.mp_hands.HandLandmark.WRIST
                ]
                middle_mcp = hand_landmarks.landmark[
                    self_instance.mp_hands.HandLandmark.MIDDLE_FINGER_MCP
                ]
                current_hand_size = math.sqrt(
                    (wrist.x - middle_mcp.x) ** 2 + (wrist.y - middle_mcp.y) ** 2
                )

                # Calculate depth ratio
                depth_ratio = (
                    current_hand_size / self_instance.depth_reference["initial_size"]
                )

                # Adjust bounds based on depth
                if depth_ratio != 1.0:
                    # Scale bounds around center point
                    initial_bounds = self_instance.depth_reference["initial_bounds"]

                    # Calculate centers
                    center_x = (initial_bounds["left"] + initial_bounds["right"]) / 2
                    center_y = (initial_bounds["top"] + initial_bounds["bottom"]) / 2

                    # Calculate new widths/heights
                    new_width = (
                        initial_bounds["right"] - initial_bounds["left"]
                    ) * depth_ratio
                    new_height = (
                        initial_bounds["bottom"] - initial_bounds["top"]
                    ) * depth_ratio

                    # Update bound scrollers
                    self_instance.left_bound_scroller.set(center_x - new_width / 2)
                    self_instance.right_bound_scroller.set(center_x + new_width / 2)
                    self_instance.top_bound_scroller.set(center_y - new_height / 2)
                    self_instance.bottom_bound_scroller.set(center_y + new_height / 2)

        if current_click != mouse_pressed:
            if current_click:
                pyautogui.mouseDown()
                mouse_pressed = True
            else:
                pyautogui.mouseUp()
                mouse_pressed = False

        if not results.multi_hand_landmarks and mouse_pressed:
            pyautogui.mouseUp()
            mouse_pressed = False

        # Get current label size for dynamic image scaling
        label_width = self_instance.webcam_image_label.winfo_width()
        label_height = self_instance.webcam_image_label.winfo_height()

        # Ensure minimum dimensions
        display_width = max(int(self_instance.frame_width * 0.6), 800)
        display_height = max(
            int(self_instance.frame_height * 0.6), 450
        )  # Maintains 16:9 aspect ratio

        # Create scaled CTkImage
        captured_image = Image.fromarray(opencv_image)
        photo_image = customtkinter.CTkImage(
            light_image=captured_image,
            dark_image=captured_image,
            size=(display_width, display_height),
        )

        # Update the label with the new image
        self_instance.webcam_image_label.configure(image=photo_image)
        self_instance.webcam_image_label.photo_image = photo_image

        # Limit the frame rate to 30 FPS
        elapsed_time = time.time() - start_time
        time.sleep(max(0, 1 / 30 - elapsed_time))

    self_instance.close_camera()


def close_camera(self_instance):
    """Safely close the camera and cleanup resources"""
    # Stop camera first
    self_instance.camera_running = False
    self_instance.stop_event.set()

    # Release camera resources
    if self_instance.cap is not None:
        self_instance.cap.release()
        self_instance.cap = None
    cv2.destroyAllWindows()

    # Ensure we're in the main thread for UI updates
    def update_ui():
        if hasattr(self_instance, "webcam_image_label"):
            try:
                self_instance.webcam_image_label.destroy()
                self_instance.webcam_image_label = customtkinter.CTkLabel(
                    self_instance.tabview.tab("Webcam Image"), text="Webcam Image"
                )
                self_instance.webcam_image_label.grid(row=4, column=0, columnspan=4)
                self_instance.open_camera_btn.configure(state="normal")
                self_instance.close_camera_btn.configure(state="disabled")
            except Exception as e:
                print(f"Error updating UI: {e}")

    # Schedule UI update for next mainloop iteration
    self_instance.after(100, update_ui)
