# Imports for GUI library and styling system
import base64
import os
from dotenv import load_dotenv
import tkinter
import tkinter.messagebox
import tkinter.ttk
import customtkinter
from tkinter import colorchooser, filedialog
from PIL import ImageGrab, Image, ImageTk
import time
import collections
import pywinstyles

# Import TextEntryWindow
from GUI.TextEntry import TextEntryWindow
from GUI.BaseGUI import BaseGUI

# Import Function Modules
from utilities import Utilities

# Imports for hand tracking and mouse manipulation
import math
import pyautogui
import mediapipe as mp
import cv2

# General Imports
import numpy as np
import threading

## Import for AI Image Generation
import replicate

from config import (
    DEFAULT_FRAME_WIDTH,
    DEFAULT_FRAME_HEIGHT,
    MIN_FRAME_WIDTH,
    MIN_FRAME_HEIGHT,
    ASPECT_RATIO,
    VELOCITY_THRESHOLD_X,
    VELOCITY_THRESHOLD_Y,
    BASE_SLOW_FACTOR,
    MIN_BOUND_SIZE,
    DEFAULT_APPEARANCE_MODE,
    DEFAULT_COLOR_THEME,
    TOOL_DICT,
    AI_MODELS,
    DEFAULT_AI_MODEL,
)

from functions.toolbarFunctions import choose_color, set_element_size, set_active_tool
from functions.canvasMouseFunctions import (
    mouse_move,
    update_temp_bbox,
    canvas_mouse_down,
    canvas_mouse_release,
)
from functions.layerPanelFunctions import (
    add_layer_to_panel,
    delete_layer,
    reposition_layers,
    select_layer,
    edit_layer_color,
)
from functions.webcamFunctions import (
    list_available_cameras,
    change_camera,
    toggle_camera_flip,
    open_camera,
    camera_loop,
    close_camera,
)

customtkinter.set_appearance_mode(DEFAULT_APPEARANCE_MODE)
customtkinter.set_default_color_theme(DEFAULT_COLOR_THEME)


class Holo(BaseGUI):
    mouse_down = False
    hex_color = "#000000"
    element_size = 5
    tool_dict = TOOL_DICT
    active_tool = "Circle Brush"
    mouse_active_coords = {
        "previous": None,
        "current": None,
    }

    stroke_counter = 0

    transform_active = False
    transform_tags = []

    active_bbox = None

    mouse_down_canvas_coords = (0, 0)
    mouse_release_canvas_coords = (0, 0)

    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles

    canvas_text = None

    screen_width, screen_height = pyautogui.size()
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0

    current_click = True

    # Mouse velocity tracking
    previous_mouse_pos = (0, 0)
    velocity_threshold_x = VELOCITY_THRESHOLD_X
    velocity_threshold_y = VELOCITY_THRESHOLD_Y
    base_slow_factor = BASE_SLOW_FACTOR
    min_bound_size = MIN_BOUND_SIZE

    # Separate X and Y velocity tracking
    # (Removed duplicate definition of previous_mouse_pos)

    def __init__(self):
        super().__init__()
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

        # Smoothing parameters
        self.mouse_smoothing = 5
        self.mouse_x_positions = collections.deque(maxlen=self.mouse_smoothing)
        self.mouse_y_positions = collections.deque(maxlen=self.mouse_smoothing)

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

        # Dictionary to store layer buttons
        self.layer_buttons = {}

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

        # Initialize tool-specific counters
        self.tool_counters = {"brush": 0, "rect": 0, "fill": 0, "text": 0, "image": 0}

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

    ########################################################################################################################################################
    ########################################################################################################################################################
    # End of init ##########################################################################################################################################
    ########################################################################################################################################################
    ########################################################################################################################################################

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

    ################################
    # Toolbar Functions
    ################################

    def choose_color(self, event):
        choose_color(self, event)

    def set_element_size(self, event):
        set_element_size(self, event)

    def set_active_tool(self, *args):
        set_active_tool(self, *args)

    def open_text_entry_window(
        self,
    ):
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = TextEntryWindow(
                self
            )  # create window if its None or destroyed
        else:
            self.toplevel_window.focus()  # if window exists focus it

    def set_canvas_text(self, entry_text):
        self.canvas_text = entry_text
        stroke_tag = self.get_stroke_tag("Text Tool")
        self.canvas.create_text(
            self.mouse_release_canvas_coords[0],
            self.mouse_release_canvas_coords[1],
            text=entry_text,
            font=customtkinter.CTkFont(size=self.element_size),
            tags=stroke_tag,
        )
        self.add_layer_to_panel(stroke_tag)

    ################################
    # Canvas Drawing Events
    ################################

    def mouse_move(self, event):
        mouse_move(self, event)

    def update_temp_bbox(self, event):
        update_temp_bbox(self, event)

    def canvas_mouse_down(self, event):
        canvas_mouse_down(self, event)

    def canvas_mouse_release(self, event):
        canvas_mouse_release(self, event)

    ################################
    # Layer Window
    ################################
    def add_layer_to_panel(self, stroke_tag):
        add_layer_to_panel(self, stroke_tag)

    def delete_layer(self, stroke_tag):
        delete_layer(self, stroke_tag)

    def reposition_layers(self):
        reposition_layers(self)

    def select_layer(self, stroke_tag):
        select_layer(self, stroke_tag)

    def edit_layer_color(self, stroke_tag):
        edit_layer_color(self, stroke_tag)

    ################################
    # Canvas Saving and AI Generation
    ################################
    def generate_ai_image(self):
        self.canvas_save_png()
        input_image_path = self.file_path
        prompt = self.prompt_entry.get()
        cv2.imshow("Input Sketch", cv2.imread(input_image_path))
        print(prompt)

        def run_replicate():
            with open(input_image_path, "rb") as file:
                data = base64.b64encode(file.read()).decode("utf-8")
                image = f"data:application/octet-stream;base64,{data}"

            replicate.Client(api_token=os.environ["REPLICATE_API_TOKEN"])

            if self.ai_model.get() == "Sketch to Image":
                output = replicate.run(
                    "qr2ai/outline:6f713aeb58eb5034ad353de02d7dd56c9efa79f2214e6b89a790dad8ca67ef49",
                    input={
                        "seed": 0,
                        "image": image,
                        "width": 1280,
                        "height": 720,
                        "prompt": prompt,
                        "sampler": "Euler a",
                        "blur_size": 3,
                        "use_canny": False,
                        "lora_input": "",
                        "lora_scale": "",
                        "kernel_size": 3,
                        "num_outputs": 1,
                        "sketch_type": "HedPidNet",
                        "suffix_prompt": "Imagine the harmonious blend of graceful forms and cosmic elegance, where each curve and line tells a story amidst the celestial backdrop, captured in a luxurious interplay of dark and light hues.",
                        "guidance_scale": 7.5,
                        "weight_primary": 0.7,
                        "generate_square": False,
                        "negative_prompt": "worst quality, low quality, low resolution, blurry, ugly, disfigured, uncrafted, filled ring, packed ring, cross, star, distorted, stagnant, watermark",
                        "weight_secondary": 0.6,
                        "erosion_iterations": 2,
                        "dilation_iterations": 1,
                        "num_inference_steps": 35,
                        "adapter_conditioning_scale": 0.9,
                    },
                )
            elif self.ai_model.get() == "t2i-adapter-sdxl-sketch":
                output = replicate.run(
                    "black-forest-labs/flux-schnell",
                    input={
                        "prompt": prompt,
                        "megapixels": "1",
                        "num_outputs": 1,
                        "aspect_ratio": "16:9",
                        "output_format": "png",
                        "output_quality": 80,
                        "num_inference_steps": 4,
                    },
                )
            else:  # T2I Adapter SDXL Sketch
                output = replicate.run(
                    "adirik/t2i-adapter-sdxl-sketch:3a14a915b013decb6ab672115c8bced7c088df86c2ddd0a89433717b9ec7d927",
                    input={
                        "image": image,
                        "prompt": prompt,
                        "scheduler": "K_EULER_ANCESTRAL",
                        "num_samples": 1,
                        "guidance_scale": 7.5,
                        "negative_prompt": "extra digit, fewer digits, cropped, worst quality, low quality, glitch, deformed, mutated, ugly, disfigured",
                        "num_inference_steps": 30,
                        "adapter_conditioning_scale": 0.9,
                        "adapter_conditioning_factor": 1,
                    },
                )

            # Rest of the function remains the same
            for index, item in enumerate(output):
                with open(f"output_{index}.png", "wb") as file:
                    file.write(item.read())

            ai_gen_image = cv2.imread("output_0.png")
            ai_gen_image = cv2.cvtColor(ai_gen_image, cv2.COLOR_BGR2RGB)
            ai_gen_image = Image.fromarray(ai_gen_image)
            ai_photo_image = ImageTk.PhotoImage(ai_gen_image)
            self.gen_ai_image_label.configure(text="")
            self.gen_ai_image_label.ai_photo_image = ai_photo_image
            self.gen_ai_image_label.configure(image=ai_photo_image)

        replicate_thread = threading.Thread(target=run_replicate)
        replicate_thread.start()
        # pass

    def canvas_save_png(self):
        self.canvas.delete("temp_bbox")
        self.canvas.delete("temp_rect")
        self.file_path = filedialog.asksaveasfilename(
            defaultextension="*.png",
            filetypes=(
                ("PNG Files", "*.png"),
                ("JPG Files", "*.jpg"),
            ),
        )
        ImageGrab.grab(
            bbox=(
                self.canvas.winfo_rootx(),
                self.canvas.winfo_rooty(),
                self.canvas.winfo_rootx() + self.canvas.winfo_width() - 4,
                self.canvas.winfo_rooty() + self.canvas.winfo_height() - 4,
            )
        ).save(self.file_path)

    ################################
    # Webcam Functions
    ################################

    def list_available_cameras(self):
        return list_available_cameras(self)

    def change_camera(self, selection):
        change_camera(self, selection)

    def toggle_camera_flip(self):
        toggle_camera_flip(self)

    def open_camera(self):
        open_camera(self)

    def camera_loop(self):
        camera_loop(self)

    def close_camera(self):
        close_camera(self)

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

    ################################
    # Helper functions
    ################################
    def getPixelPos(self, floatCoord, frameDim):
        return floatCoord * frameDim

    def place_image(self, file_path, x, y):
        """Place an image on the canvas centered at the click position"""
        # Load and convert the image
        image = Image.open(file_path)

        # Calculate scaling to fit canvas while maintaining aspect ratio
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        img_width, img_height = image.size

        # Calculate scale factor
        width_ratio = canvas_width / img_width
        height_ratio = canvas_height / img_height
        scale_factor = min(width_ratio, height_ratio) * 0.8  # 80% of max size

        # Scale image
        new_width = int(img_width * scale_factor)
        new_height = int(img_height * scale_factor)
        image = image.resize((new_width, new_height), Image.LANCZOS)

        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(image)

        # Calculate centered position
        x_centered = x - (new_width // 2)
        y_centered = y - (new_height // 2)

        # Create image on canvas
        stroke_tag = self.get_stroke_tag(self.active_tool)

        image_id = self.canvas.create_image(
            x_centered,
            y_centered,
            image=photo,
            anchor="nw",
            tags=stroke_tag,
        )

        # Keep reference to prevent garbage collection
        self.canvas.photo = photo

        # Add to layer panel
        self.add_layer_to_panel(stroke_tag)

    def get_stroke_tag(self, tool_name):
        """Generate a tag based on the tool and its specific counter"""
        tool_prefix = {
            "Circle Brush": "brush",
            "Rectangle Tool": "rect",
            "Fill Tool": "fill",
            "Text Tool": "text",
            "Image Tool": "image",
            "Calligraphy": "calli",  # Add calligraphy prefix
        }
        prefix = tool_prefix.get(tool_name, "element")
        if prefix not in self.tool_counters:
            self.tool_counters[prefix] = 0  # Initialize counter if needed
        self.tool_counters[prefix] += 1
        return f"{prefix}_{self.tool_counters[prefix]}"

    def set_transform_mode(self, mode):
        """Set the current transform mode and update button appearances"""
        self.transform_mode = mode

        # Update button colors (remove rotate from buttons dictionary)
        buttons = {"move": self.move_btn, "scale": self.scale_btn}

        for btn_mode, btn in buttons.items():
            if btn_mode == mode:
                btn.configure(fg_color="#4477AA")
            else:
                btn.configure(fg_color="transparent")

    def transform_element(self, event):
        """Handle element transformation based on current mode"""
        if not self.transform_active or not self.transform_tags:
            return

        match self.transform_mode:
            case "move":
                # Existing move logic
                dx = event.x - self.mouse_down_canvas_coords[0]
                dy = event.y - self.mouse_down_canvas_coords[1]
                for tag in self.transform_tags:
                    self.canvas.move(tag, dx, dy)
                self.canvas.move("temp_bbox", dx, dy)

            case "scale":
                # Scale from center
                for tag in self.transform_tags:
                    bbox = self.canvas.bbox(tag)
                    if bbox:
                        center_x = (bbox[0] + bbox[2]) / 2
                        center_y = (bbox[1] + bbox[3]) / 2

                        # Prevent division by zero and invalid scaling
                        try:
                            dx = event.x - center_x
                            dy = event.y - center_y
                            old_dx = self.mouse_down_canvas_coords[0] - center_x
                            old_dy = self.mouse_down_canvas_coords[1] - center_y

                            # Calculate distance ratios for scaling
                            new_dist = math.sqrt(dx * dx + dy * dy)
                            old_dist = math.sqrt(old_dx * old_dx + old_dy * old_dy)

                            if old_dist > 0:  # Prevent division by zero
                                scale = new_dist / old_dist
                                # Limit scale factor to reasonable range
                                scale = max(0.1, min(scale, 10.0))
                                self.canvas.scale(tag, center_x, center_y, scale, scale)
                        except (ZeroDivisionError, ValueError):
                            pass  # Skip scaling if calculations are invalid

        # Update mouse position for next frame
        self.mouse_down_canvas_coords = (event.x, event.y)

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

    def update_smoothing(self, value):
        """Update smoothing window size"""
        self.mouse_smoothing = int(value)
        self.mouse_x_positions = collections.deque(maxlen=self.mouse_smoothing)
        self.mouse_y_positions = collections.deque(maxlen=self.mouse_smoothing)

    def update_detection_confidence(self, value):
        """Update hand detection confidence threshold"""
        if hasattr(self, "hands"):
            self.hands.close()
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=float(value),
            min_tracking_confidence=self.tracking_slider.get(),
        )

    def update_tracking_confidence(self, value):
        """Update hand tracking confidence threshold"""
        if hasattr(self, "hands"):
            self.hands.close()
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=self.detection_slider.get(),
            min_tracking_confidence=float(value),
        )

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
                    x_pos = palm.x * self.frame_width
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
                    x_pos = palm.x * self.frame_width
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
                    y_pos = palm.y * self.frame_height
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
                    y_pos = palm.y * self.frame_height
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

    def toggle_mouse_control(self):
        """Toggle mouse control on/off"""
        self.mouse_control_enabled = self.mouse_control.get()

    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode"""
        if self.state() == "zoomed":
            self.state("normal")
        else:
            self.state("zoomed")


if __name__ == "__main__":
    app = Holo()
    app.mainloop()
