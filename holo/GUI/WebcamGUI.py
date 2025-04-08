import customtkinter

from config import DEFAULT_FRAME_HEIGHT, DEFAULT_FRAME_WIDTH


class WebcamGUI:
    def __init__(self):
        # Webcam Tab
        self.tabview.tab("Webcam Image").columnconfigure((0, 1, 2, 3), weight=1)
        self.tabview.tab("Webcam Image").rowconfigure(4, weight=1)

        # Camera controls frame - left side
        self.camera_controls_frame = customtkinter.CTkFrame(
            self.tabview.tab("Webcam Image")
        )
        self.camera_controls_frame.grid(row=0, column=0, padx=5, pady=5)
        self.webcam_selection_label = customtkinter.CTkLabel(
            self.camera_controls_frame, text="Webcam Settings"
        )
        self.webcam_selection_label.grid(row=0, column=0, columnspan=2, padx=5, pady=5)
        self.camera_controls_frame.grid_columnconfigure(0, weight=1)

        # Camera selection dropdown
        self.available_cameras = self.list_available_cameras()
        self.camera_select = customtkinter.CTkOptionMenu(
            self.camera_controls_frame,
            values=[f"Camera {i}" for i in self.available_cameras],
            command=self.change_camera,
        )
        self.camera_select.grid(row=1, column=0, padx=5, pady=5)

        # Flip camera toggle below dropdown
        self.flip_camera = customtkinter.CTkCheckBox(
            self.camera_controls_frame,
            text="Flip Camera",
            command=self.toggle_camera_flip,
        )
        self.flip_camera.grid(row=2, column=0, padx=5, pady=5)

        # Add after the flip camera toggle in __init__
        self.mouse_control = customtkinter.CTkCheckBox(
            self.camera_controls_frame,
            text="Mouse Control",
            command=self.toggle_mouse_control,
        )
        self.mouse_control.grid(row=3, column=0, padx=5, pady=5)

        # Bounds control frame - right side
        self.bounds_frame = customtkinter.CTkFrame(self.tabview.tab("Webcam Image"))
        self.bounds_frame.grid(row=0, column=2, columnspan=2, padx=5, pady=5)

        # X, Y position controls
        self.bound_pos_label = customtkinter.CTkLabel(
            self.bounds_frame, text="Bounding Box Edges:"
        )
        self.bound_pos_label.grid(row=0, column=0, columnspan=2, padx=5, pady=2)

        # Left bound
        self.left_bound_scroller = customtkinter.CTkSlider(
            self.bounds_frame,
            width=200,
            from_=0,
            to=int(DEFAULT_FRAME_WIDTH),
        )
        self.left_bound_scroller.grid(row=1, column=0, padx=5, pady=2)
        self.left_bound_label = customtkinter.CTkLabel(self.bounds_frame, text="Left")
        self.left_bound_label.grid(row=2, column=0)

        # Right bound
        self.right_bound_scroller = customtkinter.CTkSlider(
            self.bounds_frame,
            width=200,
            from_=0,
            to=int(DEFAULT_FRAME_WIDTH),
        )
        self.right_bound_scroller.grid(row=1, column=1, padx=5, pady=2)
        self.right_bound_label = customtkinter.CTkLabel(self.bounds_frame, text="Right")
        self.right_bound_label.grid(row=2, column=1)

        # Top bound
        self.top_bound_scroller = customtkinter.CTkSlider(
            self.bounds_frame,
            width=200,
            from_=0,
            to=int(DEFAULT_FRAME_HEIGHT),
        )
        self.top_bound_scroller.grid(row=3, column=0, padx=5, pady=2)
        self.top_bound_label = customtkinter.CTkLabel(self.bounds_frame, text="Top")
        self.top_bound_label.grid(row=4, column=0)

        # Bottom bound
        self.bottom_bound_scroller = customtkinter.CTkSlider(
            self.bounds_frame,
            width=200,
            from_=0,
            to=int(DEFAULT_FRAME_HEIGHT),
        )
        self.bottom_bound_scroller.grid(row=3, column=1, padx=5, pady=2)
        self.bottom_bound_label = customtkinter.CTkLabel(
            self.bounds_frame, text="Bottom"
        )
        self.bottom_bound_label.grid(row=4, column=1)

        # Set default values for bounds
        self.left_bound_scroller.set(0)  # Left at 0
        self.right_bound_scroller.set(DEFAULT_FRAME_WIDTH)  # Right at max width
        self.top_bound_scroller.set(0)  # Top at 0
        self.bottom_bound_scroller.set(DEFAULT_FRAME_HEIGHT)  # Bottom at max height

        # Camera view
        self.webcam_image_label = customtkinter.CTkLabel(
            self.tabview.tab("Webcam Image"),
            text="Waiting for Camera Feed",
            fg_color="transparent",
        )
        self.webcam_image_label.grid(row=4, column=0, columnspan=4)

        self.open_camera_btn = customtkinter.CTkButton(
            self.tabview.tab("Webcam Image"),
            text="Open Camera",
            command=self.open_camera,
            width=100,
        )
        self.open_camera_btn.grid(row=5, column=0, padx=5, pady=5)
        self.close_camera_btn = customtkinter.CTkButton(
            self.tabview.tab("Webcam Image"),
            text="Close Camera",
            state="disabled",
            command=self.close_camera,
            width=100,
        )
        self.close_camera_btn.grid(row=5, column=1, padx=5, pady=5)

        # Auto Configure Hand Bounds
        self.auto_configure_bound_frame = customtkinter.CTkFrame(
            self.tabview.tab("Webcam Image")
        )
        self.auto_configure_bound_frame.grid(
            row=5, column=2, columnspan=2, padx=5, pady=5
        )

        self.depth_btn = customtkinter.CTkButton(
            self.auto_configure_bound_frame,
            command=self.configure_depth,
            text="Calibrate Depth",
            width=100,
        )
        self.depth_btn.grid(row=1, column=1, padx=5, pady=5)
        self.left_bound_btn = customtkinter.CTkButton(
            self.auto_configure_bound_frame,
            command=self.auto_configure_left_bound,
            text="Left Bound",
            width=100,
        )
        self.left_bound_btn.grid(row=1, column=0, padx=5, pady=5)
        self.right_bound_btn = customtkinter.CTkButton(
            self.auto_configure_bound_frame,
            command=self.auto_configure_right_bound,
            text="Right Bound",
            width=100,
        )
        self.right_bound_btn.grid(row=1, column=2, padx=5, pady=5)

        self.top_bound_btn = customtkinter.CTkButton(
            self.auto_configure_bound_frame,
            command=self.auto_configure_top_bound,
            text="Top Bound",
            width=100,
        )
        self.top_bound_btn.grid(row=0, column=1, padx=5, pady=5)

        self.bottom_bound_btn = customtkinter.CTkButton(
            self.auto_configure_bound_frame,
            command=self.auto_configure_bottom_bound,
            text="Bottom Bound",
            width=100,
        )
        self.bottom_bound_btn.grid(row=2, column=1, padx=5, pady=5)

        # Add webcam settings frame
        self.webcam_settings_frame = customtkinter.CTkFrame(
            self.tabview.tab("Webcam Image")
        )
        self.webcam_settings_frame.grid(row=0, column=1, padx=5, pady=5)

        # Settings label
        self.settings_label = customtkinter.CTkLabel(
            self.webcam_settings_frame,
            text="Tracking Settings",
            font=customtkinter.CTkFont(size=14, weight="bold"),
        )
        self.settings_label.grid(row=0, column=0, columnspan=2, padx=5, pady=5)

        # Smoothing window size
        self.smoothing_label = customtkinter.CTkLabel(
            self.webcam_settings_frame, text="Mouse Smoothing:"
        )
        self.smoothing_label.grid(row=1, column=0, padx=5, pady=2)

        self.smoothing_slider = customtkinter.CTkSlider(
            self.webcam_settings_frame,
            from_=1,
            to=20,
            number_of_steps=19,
            command=self.update_smoothing,
        )
        self.smoothing_slider.set(self.mouse_smoothing)
        self.smoothing_slider.grid(row=1, column=1, padx=5, pady=2)

        # Detection confidence
        self.detection_label = customtkinter.CTkLabel(
            self.webcam_settings_frame, text="Detection Confidence:"
        )
        self.detection_label.grid(row=2, column=0, padx=5, pady=2)

        self.detection_slider = customtkinter.CTkSlider(
            self.webcam_settings_frame,
            from_=0.1,
            to=1.0,
            number_of_steps=18,
            command=self.update_detection_confidence,
        )
        self.detection_slider.set(0.5)  # Default value
        self.detection_slider.grid(row=2, column=1, padx=5, pady=2)

        # Tracking confidence
        self.tracking_label = customtkinter.CTkLabel(
            self.webcam_settings_frame, text="Tracking Confidence:"
        )
        self.tracking_label.grid(row=3, column=0, padx=5, pady=2)

        self.tracking_slider = customtkinter.CTkSlider(
            self.webcam_settings_frame,
            from_=0.1,
            to=1.0,
            number_of_steps=18,
            command=self.update_tracking_confidence,
        )
        self.tracking_slider.set(0.5)  # Default value
        self.tracking_slider.grid(row=3, column=1, padx=5, pady=2)
