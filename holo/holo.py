# Imports for GUI library and styling system
import ctypes
from dotenv import load_dotenv
import tkinter
import customtkinter
from PIL import Image

from GUI.BaseGUI import BaseGUI
from functions.canvasMouseFunctions import CanvasMouseFunctions
from functions.layerPanelFunctions import LayerPanelFunctions
from functions.webcamFunctions import WebcamFunctions
from functions.toolbarFunctions import ToolbarFunctions
from functions.handTrackingCalibrationFunctions import HandTrackingCalibrationFunctions
from functions.textFunctions import TextFunctions
from functions.canvasSavingFunctions import CanvasSavingFunctions
from functions.windowHelperFunctions import WindowHelperFunctions

# Imports for hand tracking and mouse manipulation
import pyautogui

# General Imports
import threading

from config import (
    DEFAULT_FRAME_WIDTH,
    DEFAULT_FRAME_HEIGHT,
    DEFAULT_APPEARANCE_MODE,
    DEFAULT_COLOR_THEME,
    AI_MODELS,
    DEFAULT_AI_MODEL,
)

ctypes.windll.shcore.SetProcessDpiAwareness(1)
customtkinter.set_appearance_mode(DEFAULT_APPEARANCE_MODE)
customtkinter.set_default_color_theme(DEFAULT_COLOR_THEME)


class Holo(
    CanvasMouseFunctions,
    LayerPanelFunctions,
    WebcamFunctions,
    ToolbarFunctions,
    TextFunctions,
    HandTrackingCalibrationFunctions,
    BaseGUI,
    CanvasSavingFunctions,
    WindowHelperFunctions,
):

    canvas_text = None

    screen_width, screen_height = pyautogui.size()
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0

    def __init__(self):
        super().__init__()

        CanvasMouseFunctions.__init__(self)
        LayerPanelFunctions.__init__(self)
        WebcamFunctions.__init__(self)
        TextFunctions.__init__(self)
        ToolbarFunctions.__init__(self)
        HandTrackingCalibrationFunctions.__init__(self)

        BaseGUI.__init__(self)

        load_dotenv()

        # Capture Components
        self.cap = None  # Initialize as None instead of with specific index
        self.frame_width, self.frame_height = DEFAULT_FRAME_WIDTH, DEFAULT_FRAME_HEIGHT

        self.camera_thread = None
        self.camera_running = False
        self.stop_event = threading.Event()

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,  # Already set correctly
            max_num_hands=1,  # Already set correctly
            min_detection_confidence=0.5,  # Lower this from 0.7
            min_tracking_confidence=0.5,  # Lower this from 0.7
        )

        # Canvas Frame with dynamic sizing
        self.canvas_frame = customtkinter.CTkFrame(
            self.tabview.tab("Canvas"),
            fg_color="transparent",
        )
        self.canvas_frame.grid(
            row=1, column=0, columnspan=3, sticky="nsew", padx=10, pady=10
        )
        self.canvas_frame.grid_columnconfigure(0, weight=1)
        self.canvas_frame.grid_rowconfigure(0, weight=1)

        # Create canvas with dynamic sizing
        self.canvas = customtkinter.CTkCanvas(
            self.canvas_frame,
            bg="white",
            cursor="circle",
        )
        self.canvas.place(relx=0.5, rely=0.5, anchor="center", width=1280, height=720)

        # Bind resize event
        self.bind("<Configure>", self.on_window_resize)

        # Canvas Mouse Events
        self.canvas.bind("<Button-1>", self.canvas_mouse_down)
        self.canvas.bind("<ButtonRelease-1>", self.canvas_mouse_release)
        self.canvas.bind("<Motion>", self.mouse_move)

        # Create transform controls container but don't show it initially
        self.transform_controls = customtkinter.CTkFrame(self.tabview.tab("Canvas"))

        # Create transform mode buttons
        self.transform_mode = tkinter.StringVar(value="move")

        self.move_btn = customtkinter.CTkButton(
            self.transform_controls,
            text="Move",
            width=100,
            command=lambda: self.set_transform_mode("move"),
            fg_color="#4477AA",
        )
        self.move_btn.grid(row=0, column=0, padx=5, pady=5)

        self.scale_btn = customtkinter.CTkButton(
            self.transform_controls,
            text="Scale",
            width=100,
            command=lambda: self.set_transform_mode("scale"),
            fg_color="transparent",
        )
        self.scale_btn.grid(row=0, column=1, padx=5, pady=5)

        # Generation and Saving Buttons
        self.prompt_entry = customtkinter.CTkEntry(
            self.tabview.tab("Canvas"),
            placeholder_text="Prompt to guide image generation...",
        )
        self.prompt_entry.grid(
            row=2, column=0, padx=(20, 20), pady=(10, 10), sticky="ew"
        )
        self.generate_ai_image_btn = customtkinter.CTkButton(
            master=self.tabview.tab("Canvas"),
            fg_color="transparent",
            border_width=2,
            text="Generated AI Image",
            text_color=("gray10", "#DCE4EE"),
            command=self.generate_ai_image,
        )
        self.generate_ai_image_btn.grid(
            row=2, column=1, padx=(20, 20), pady=(20, 20), sticky="ew"
        )
        self.save_canvas = customtkinter.CTkButton(
            master=self.tabview.tab("Canvas"),
            fg_color="transparent",
            border_width=2,
            text="Save Drawing",
            text_color=("gray10", "#DCE4EE"),
            command=self.canvas_save_png,
        )
        self.save_canvas.grid(
            row=2, column=2, padx=(20, 20), pady=(20, 20), sticky="ew"
        )

        # Add layer panel frame
        self.layer_panel = customtkinter.CTkFrame(
            self.tabview.tab("Canvas"), corner_radius=0
        )
        self.layer_panel.grid(row=0, column=3, rowspan=3, sticky="nsew", padx=5, pady=5)
        self.layer_panel.grid_columnconfigure(0, weight=1)
        self.layer_panel.grid_rowconfigure(1, weight=1)

        # Add layer panel label
        self.layer_panel_label = customtkinter.CTkLabel(
            self.layer_panel,
            text="Layers",
            font=customtkinter.CTkFont(size=16, weight="bold"),
        )
        self.layer_panel_label.grid(row=0, column=0, pady=5, padx=5)

        # Add scrollable frame for layers
        self.layer_container = customtkinter.CTkScrollableFrame(
            self.layer_panel,
        )
        self.layer_container.grid(row=1, column=0, pady=5, padx=5, sticky="nsew")

        # Generated AI Image Tab
        self.tabview.tab("Generated AI Image").columnconfigure(0, weight=1)
        self.tabview.tab("Generated AI Image").rowconfigure(
            1, weight=1
        )  # Changed from 0 to 1

        # Add model selection frame
        self.model_select_frame = customtkinter.CTkFrame(
            self.tabview.tab("Generated AI Image")
        )
        self.model_select_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        # Add model selection dropdown
        self.ai_model = tkinter.StringVar(value=DEFAULT_AI_MODEL)
        self.model_select = customtkinter.CTkOptionMenu(
            self.model_select_frame,
            values=AI_MODELS,
            variable=self.ai_model,
            width=200,
        )
        self.model_select.grid(row=0, column=0, padx=5, pady=5)

        # Move existing label to row 1
        self.gen_ai_image_label = customtkinter.CTkLabel(
            self.tabview.tab("Generated AI Image"),
            text="Waiting for AI Generated Image (this may take time)",
        )
        self.gen_ai_image_label.grid(row=1, column=0)

        # Add this where your gen_ai_image_label is created in __init__
        self.copy_to_canvas_btn = customtkinter.CTkButton(
            master=self.tabview.tab("Generated AI Image"),
            fg_color="transparent",
            border_width=2,
            text="Copy to Canvas",
            text_color=("gray10", "#DCE4EE"),
            command=self.copy_ai_image_to_canvas,
            state="disabled",  # Initially disabled until an image is generated
        )
        self.copy_to_canvas_btn.grid(
            row=2, column=0, padx=(20, 20), pady=(5, 20), sticky="ew"
        )

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
            to=int(self.frame_width),
        )
        self.left_bound_scroller.grid(row=1, column=0, padx=5, pady=2)
        self.left_bound_label = customtkinter.CTkLabel(self.bounds_frame, text="Left")
        self.left_bound_label.grid(row=2, column=0)

        # Right bound
        self.right_bound_scroller = customtkinter.CTkSlider(
            self.bounds_frame,
            width=200,
            from_=0,
            to=int(self.frame_width),
        )
        self.right_bound_scroller.grid(row=1, column=1, padx=5, pady=2)
        self.right_bound_label = customtkinter.CTkLabel(self.bounds_frame, text="Right")
        self.right_bound_label.grid(row=2, column=1)

        # Top bound
        self.top_bound_scroller = customtkinter.CTkSlider(
            self.bounds_frame,
            width=200,
            from_=0,
            to=int(self.frame_height),
        )
        self.top_bound_scroller.grid(row=3, column=0, padx=5, pady=2)
        self.top_bound_label = customtkinter.CTkLabel(self.bounds_frame, text="Top")
        self.top_bound_label.grid(row=4, column=0)

        # Bottom bound
        self.bottom_bound_scroller = customtkinter.CTkSlider(
            self.bounds_frame,
            width=200,
            from_=0,
            to=int(self.frame_height),
        )
        self.bottom_bound_scroller.grid(row=3, column=1, padx=5, pady=2)
        self.bottom_bound_label = customtkinter.CTkLabel(
            self.bounds_frame, text="Bottom"
        )
        self.bottom_bound_label.grid(row=4, column=1)

        # Set default values for bounds
        self.left_bound_scroller.set(0)  # Left at 0
        self.right_bound_scroller.set(self.frame_width)  # Right at max width
        self.top_bound_scroller.set(0)  # Top at 0
        self.bottom_bound_scroller.set(self.frame_height)  # Bottom at max height

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

        # ################################
        # ################################
        # # create main entry and button
        # ################################
        # ################################

        # set default values
        self.appearance_mode_optionemenu.set("Dark")
        self.scaling_optionemenu.set("100%")

        # Load icons
        self.trash_icon = customtkinter.CTkImage(
            light_image=Image.open("./assets/images/trash-icon-black.png"),
            dark_image=Image.open("./assets/images/trash-icon-white.png"),
        )
        self.edit_icon = customtkinter.CTkImage(
            light_image=Image.open("./assets/images/edit-icon-black.png"),
            dark_image=Image.open("./assets/images/edit-icon-white.png"),
        )

        self.apply_win_style("acrylic")


if __name__ == "__main__":
    app = Holo()
    app.mainloop()
