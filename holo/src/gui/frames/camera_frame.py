import customtkinter
import cv2
from PIL import Image, ImageTk
from ...camera.camera_manager import CameraManager
from ...config.settings import CameraSettings


class CameraFrame(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.camera_manager = CameraManager()
        self._setup_ui()

    def _setup_ui(self):
        # Camera controls
        self.controls_frame = customtkinter.CTkFrame(self)
        self.controls_frame.grid(row=0, column=1, padx=5, pady=5, sticky="n")

        # Camera selection
        self._setup_camera_controls()

        # Camera view
        self.webcam_image_label = customtkinter.CTkLabel(self, text="Camera Off")
        self.webcam_image_label.grid(row=1, column=0, columnspan=3, sticky="nsew")

    def _setup_camera_controls(self):
        """Setup camera controls"""
        # Camera selection dropdown
        available_cameras = self.camera_manager.list_available_cameras()
        self.camera_select = customtkinter.CTkOptionMenu(
            self.controls_frame,
            values=[f"Camera {i}" for i in available_cameras],
            command=self.camera_manager.change_camera,
        )
        self.camera_select.grid(row=1, column=0, padx=5, pady=5)
