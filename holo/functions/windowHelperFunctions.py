# Imports for GUI library and styling system
import customtkinter
import pywinstyles

# Imports for hand tracking and mouse manipulation
import cv2

from config import ASPECT_RATIO, MIN_FRAME_HEIGHT, MIN_FRAME_WIDTH

# General Imports


class WindowHelperFunctions:
    def __init__(self):
        pass

    def apply_win_style(self, style_name):
        pywinstyles.apply_style(self, style_name)
        pywinstyles.set_opacity(self.canvas, 1)
        pywinstyles.set_opacity(self.webcam_image_label, 1)
        pywinstyles.set_opacity(self.gen_ai_image_label, 1)

    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)
        if new_appearance_mode == "Light":
            self.apply_win_style("mica")
        elif new_appearance_mode == "Dark":
            self.apply_win_style("acrylic")
            pywinstyles.set_opacity(self, 1)

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        customtkinter.set_widget_scaling(new_scaling_float)

    def on_closing(self):
        if hasattr(self, "camera_running") and self.camera_running:
            # Stop the camera loop
            self.camera_running = False
            self.stop_event.set()

            # Wait for camera thread to finish
            if self.camera_thread and self.camera_thread.is_alive():
                self.camera_thread.join(timeout=1.0)

            # Release camera resources
            if self.cap and self.cap.isOpened():
                self.cap.release()
                self.cap = None

            # Cleanup OpenCV windows
            cv2.destroyAllWindows()

            # Reset camera-related variables
            self.camera_thread = None
            self.webcam_image_label.configure(text="Camera Off")

        # Clean up MediaPipe resources
        if hasattr(self, "hands"):
            self.hands.close()

        # Destroy the window
        self.quit()
        self.destroy()

    def on_window_resize(self, event):
        """Handle window resize events"""
        if event.widget == self:
            # Get the available space
            frame_width = self.canvas_frame.winfo_width()
            frame_height = self.canvas_frame.winfo_height()

            # Maintain aspect ratio
            if frame_width / frame_height > ASPECT_RATIO:
                new_height = frame_height
                new_width = int(new_height * ASPECT_RATIO)
            else:
                new_width = frame_width
                new_height = int(new_width / ASPECT_RATIO)

            # Ensure minimum dimensions
            new_width = max(new_width, MIN_FRAME_WIDTH)
            new_height = max(new_height, MIN_FRAME_HEIGHT)

            # Configure canvas size
            self.canvas.configure(width=new_width, height=new_height)

    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode"""
        if self.state() == "zoomed":
            self.state("normal")
        else:
            self.state("zoomed")
