# Imports for GUI library and styling system
import base64
import os
from dotenv import load_dotenv
import sys
import tkinter
import tkinter.messagebox
import tkinter.ttk
import customtkinter
from tkinter import colorchooser, filedialog
from PIL import ImageGrab, Image, ImageTk, ImageOps
import ctypes
import time
import collections
import pywinstyles

# Imports for hand tracking and mouse manipulation
import math
import pyautogui
import mediapipe as mp
import cv2

# General Imports
import numpy as np
import threading

# Import for Speech Recognition
import vosk
import pyaudio
import json

## Import for AI Image Generation
import replicate


customtkinter.set_appearance_mode(
    "System"
)  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme(
    "./holo_theme.json"
)  # Themes: "blue" (standard), "green", "dark-blue"


class TextEntryWindow(customtkinter.CTkToplevel):

    do_stop_speech = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("720x720")
        self.title("Text Entry Window")
        self.attributes("-topmost", True)
        self.attributes("-toolwindow", "True")

        self.label = customtkinter.CTkLabel(
            self,
            text="Type to enter text or use Speech Recognition",
            font=customtkinter.CTkFont(size=32),
        )
        self.text_entry = customtkinter.CTkTextbox(self)

        self.start_speech_rec_button = customtkinter.CTkButton(
            self,
            text="Start Speech Recognition",
            fg_color="#FF0000",
            hover_color="#770000",
            cursor="star",
            command=self.start_speech_rec,
        )
        self.submit_button = customtkinter.CTkButton(
            self, text="Submit Text", command=self.set_text_from_entry
        )

        self.label.pack(padx=20, pady=20)
        self.text_entry.pack(padx=20, pady=20, expand=True, fill="both")
        self.start_speech_rec_button.pack(padx=20, pady=20, expand=True, fill="both")
        self.submit_button.pack(padx=20, pady=20, expand=False, fill="x")
        self.text_entry.focus()

        self.text_entry.bind("<Return>", command=self.submit_text)

    def start_speech_rec(self):
        self.label.destroy()
        self.text_entry.destroy()
        self.start_speech_rec_button.destroy()
        self.submit_button.destroy()
        self.speech_rec_state_label = customtkinter.CTkLabel(
            self,
            text="Speech Recognition Active",
            text_color="#0000FF",
            font=customtkinter.CTkFont(size=32),
        )
        self.stop_speech_rec_button = customtkinter.CTkButton(
            self,
            text="Stop Speech Recognition",
            fg_color="#FF0000",
            hover_color="#770000",
            cursor="star",
            command=self.stop_speech_rec,
        )
        self.speech_rec_state_label.pack(padx=20, pady=20)
        self.stop_speech_rec_button.pack(padx=20, pady=20, expand=True, fill="x")

        speech_recognition_thread = threading.Thread(target=self.recognize_speech)
        speech_recognition_thread.start()

    def stop_speech_rec(self):
        self.do_stop_speech = True
        self.stop_speech_rec_button.destroy()

    def recognize_speech(self):

        speech_model_path = "vosk-model-small-en-us-0.15"
        speech_model = vosk.Model(speech_model_path)
        rec = vosk.KaldiRecognizer(speech_model, 16000)

        # Open the microphone stream
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=8192,
        )

        # Specify the path for the output text file
        output_file_path = "recognized_text.txt"

        # Open a text file in write mode using a 'with' block
        with open(output_file_path, "w") as output_file:
            # print("Listening for speech. Say 'Terminate' to stop.")
            # Start streaming and recognize speech
            while True:
                data = stream.read(4096)  # read in chunks of 4096 bytes
                if rec.AcceptWaveform(data):  # accept waveform of input voice
                    # Parse the JSON result and get the recognized text
                    result = json.loads(rec.Result())
                    recognized_text = result["text"]
                    # Check for the termination keyword
                    if (
                        "terminate" in recognized_text.lower()
                        or self.do_stop_speech
                        or not self.winfo_exists()
                    ):
                        # print("Termination keyword detected. Stopping...")
                        break

                    # Write recognized text to the file
                    output_file.write(recognized_text + "\n")
                    # print(recognized_text)

        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        # Terminate the PyAudio object
        p.terminate()

        with open(output_file_path, "r") as output_file:
            self.set_text_from_speech(output_file.read())

        if os.path.exists(output_file_path):
            os.remove(output_file_path)

    def set_text_from_entry(self):
        self.text = self.text_entry.get("0.0", "end")
        app.set_canvas_text(self.text)
        self.destroy()

    def submit_text(self, event):
        self.set_text_from_entry()

    def set_text_from_speech(self, recognized_text):
        self.text = recognized_text
        app.set_canvas_text(self.text)
        self.destroy()

    def get_text(self):
        return self.text


class Holo(customtkinter.CTk):
    mouse_down = False
    hex_color = "#000000"
    element_size = 5
    tool_dict = {
        0: "Circle Brush",
        1: "Rectangle Tool",
        2: "Fill Tool",
        3: "Text Tool",
        4: "Transform Tool",
        5: "Delete Tool",
        6: "Image Tool",  # Add this line
    }
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

    def __init__(self):
        super().__init__()

        load_dotenv()

        self.cap = None  # Initialize as None instead of with specific index
        self.frame_width, self.frame_height = 1280, 720

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

        # configure window
        self.title("Holo")
        self.geometry(f"{self.frame_width}x{self.frame_height}")
        # set a minmum size for the window
        self.minsize(1280, 720)

        # Optional: Add F11 key binding to toggle fullscreen
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", lambda e: self.on_closing())

        # Override the protocol method to detect window close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.toplevel_window = None

        self.holo_logo = tkinter.PhotoImage(file="./images/holo_transparent_scaled.png")
        myappid = "Holo"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        self.wm_iconbitmap("./images/holo_transparent_scaled.png")
        self.iconphoto(False, self.holo_logo)

        # configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        ################################
        ################################
        # create sidebar frame with widgets
        ################################
        ################################
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")

        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        self.logo_label = customtkinter.CTkLabel(
            self.sidebar_frame,
            text="Holo Tools",
            font=customtkinter.CTkFont(size=20, weight="bold"),
        )

        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.color_label = customtkinter.CTkLabel(
            self.sidebar_frame,
            text=f"Element Color: {self.hex_color}",
            fg_color=self.hex_color,
            font=("Arial", 12),
            padx=20,
            pady=5,
            corner_radius=5,
            cursor="hand2",
        )
        self.color_label.bind("<Button-1>", self.choose_color)
        self.color_label.grid(row=2, column=0, rowspan=2, padx=20, pady=(5, 50))

        self.element_size_label = customtkinter.CTkLabel(
            self.sidebar_frame,
            text=f"Element Size: {self.element_size}",
            font=("Arial", 12),
            pady=10,
        )

        self.element_size_label.grid(
            row=3,
            column=0,
            padx=(20, 10),
            pady=(10, 0),
            sticky="nsw",
        )
        self.element_size_slider = customtkinter.CTkSlider(
            self.sidebar_frame,
            from_=1,
            to=100,
            number_of_steps=100,
            command=self.set_element_size,
            progress_color="#4477AA",
        )
        self.element_size_slider.grid(row=4, column=0, padx=(20, 10), pady=(0, 10))

        # create radiobutton frame
        self.radiobutton_frame = customtkinter.CTkFrame(self.sidebar_frame)
        self.radiobutton_frame.grid(
            row=5, column=0, padx=(20, 20), pady=(20, 0), sticky="nsew"
        )
        self.radio_tool_var = tkinter.IntVar(value=0)
        self.radio_tool_var.trace_add("write", callback=self.set_active_tool)
        self.label_radio_group = customtkinter.CTkLabel(
            master=self.radiobutton_frame, text="Select Tool:"
        )
        self.label_radio_group.grid(
            row=0, column=0, columnspan=1, padx=10, pady=10, sticky="nsew"
        )

        self.radio_button_1 = customtkinter.CTkRadioButton(
            master=self.radiobutton_frame,
            variable=self.radio_tool_var,
            value=0,
            text="Circle Brush",
        )
        self.radio_button_1.grid(row=1, column=0, pady=10, padx=20, sticky="nsew")

        self.radio_button_2 = customtkinter.CTkRadioButton(
            master=self.radiobutton_frame,
            variable=self.radio_tool_var,
            value=1,
            text="Rectangle Tool",
        )
        self.radio_button_2.grid(row=2, column=0, pady=10, padx=20, sticky="nsew")
        self.radio_button_3 = customtkinter.CTkRadioButton(
            master=self.radiobutton_frame,
            variable=self.radio_tool_var,
            value=2,
            text="Fill Tool",
        )
        self.radio_button_3.grid(row=3, column=0, pady=10, padx=20, sticky="nsew")
        self.radio_button_4 = customtkinter.CTkRadioButton(
            master=self.radiobutton_frame,
            variable=self.radio_tool_var,
            value=3,
            text="Text Tool",
        )
        self.radio_button_4.grid(row=4, column=0, pady=10, padx=20, sticky="nsew")
        self.radio_button_5 = customtkinter.CTkRadioButton(
            master=self.radiobutton_frame,
            variable=self.radio_tool_var,
            value=4,
            text="Transform Tool",
        )
        self.radio_button_5.grid(row=5, column=0, pady=10, padx=20, sticky="nsew")
        self.radio_button_6 = customtkinter.CTkRadioButton(
            master=self.radiobutton_frame,
            variable=self.radio_tool_var,
            value=5,
            text="Delete Tool",
        )
        self.radio_button_6.grid(row=6, column=0, pady=10, padx=20, sticky="nsew")
        self.radio_button_7 = customtkinter.CTkRadioButton(
            master=self.radiobutton_frame,
            variable=self.radio_tool_var,
            value=6,
            text="Image Tool",
        )
        self.radio_button_7.grid(row=7, column=0, pady=10, padx=20, sticky="nsew")

        self.appearance_mode_label = customtkinter.CTkLabel(
            self.sidebar_frame, text="Appearance Mode:", anchor="w"
        )
        self.appearance_mode_label.grid(row=6, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(
            self.sidebar_frame,
            values=["Light", "Dark", "System"],
            command=self.change_appearance_mode_event,
        )
        self.appearance_mode_optionemenu.grid(row=7, column=0, padx=20, pady=(10, 10))
        self.scaling_label = customtkinter.CTkLabel(
            self.sidebar_frame, text="UI Scaling:", anchor="w"
        )
        self.scaling_label.grid(row=8, column=0, padx=20, pady=(10, 0), sticky="sw")
        self.scaling_optionemenu = customtkinter.CTkOptionMenu(
            self.sidebar_frame,
            values=["80%", "90%", "100%", "110%", "120%"],
            command=self.change_scaling_event,
        )
        self.scaling_optionemenu.grid(row=9, column=0, padx=20, pady=(10, 20))

        # Main Frame
        self.main_frame = customtkinter.CTkFrame(
            self,
            corner_radius=0,
        )
        self.main_frame.grid(row=0, rowspan=4, column=1, padx=0, pady=0, sticky="NSEW")
        self.main_ribbon = tkinter.ttk.Notebook(self.main_frame)

        # create tabview
        self.tabview = customtkinter.CTkTabview(
            self.main_frame,
            bg_color="transparent",
            fg_color="transparent",
        )
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.tabview.grid(row=0, column=0, padx=(20, 20), pady=(10, 10), sticky="NSEW")
        self.tabview.add("Canvas")
        self.tabview.add("Genrated AI Image")
        self.tabview.add("Webcam Image")

        # Canvas Tab
        # Main Frame grid configuration
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # Configure tab view grid weights
        self.tabview.grid(row=0, column=0, padx=(20, 20), pady=(10, 10), sticky="nsew")
        self.tabview.tab("Canvas").grid_columnconfigure(
            0, weight=3
        )  # Give more weight to canvas
        self.tabview.tab("Canvas").grid_columnconfigure(
            3, weight=1
        )  # Less weight for layer panel
        self.tabview.tab("Canvas").grid_rowconfigure(
            1, weight=1
        )  # Make canvas row expandable

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
            text="Generate AI Image",
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
        self.tabview.tab("Genrated AI Image").columnconfigure(0, weight=1)
        self.tabview.tab("Genrated AI Image").rowconfigure(
            1, weight=1
        )  # Changed from 0 to 1

        # Add model selection frame
        self.model_select_frame = customtkinter.CTkFrame(
            self.tabview.tab("Genrated AI Image")
        )
        self.model_select_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        # Add model selection dropdown
        self.ai_model = tkinter.StringVar(value="Sketch to Image")
        self.model_select = customtkinter.CTkOptionMenu(
            self.model_select_frame,
            values=["Sketch to Image", "Flux Schnell", "t2i-adapter-sdxl-sketch"],
            variable=self.ai_model,
            width=200,
        )
        self.model_select.grid(row=0, column=0, padx=5, pady=5)

        # Move existing label to row 1
        self.gen_ai_image_label = customtkinter.CTkLabel(
            self.tabview.tab("Genrated AI Image"),
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
            light_image=Image.open("./images/trash-icon-black.png"),
            dark_image=Image.open("./images/trash-icon-white.png"),
        )
        self.edit_icon = customtkinter.CTkImage(
            light_image=Image.open("./images/edit-icon-black.png"),
            dark_image=Image.open("./images/edit-icon-white.png"),
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
        self.color_code = colorchooser.askcolor(title="Choose color")
        if self.color_code:
            self.hex_color = self.color_code[1]
            self.color_label.configure(
                text=f"Element Color: {self.hex_color}", fg_color=self.hex_color
            )

    def set_element_size(self, event):
        self.element_size = int(self.element_size_slider.get())
        self.element_size_label.configure(text=f"Element Size: {self.element_size}")

    def set_active_tool(self, *args):
        self.active_tool = self.tool_dict.get(self.radio_tool_var.get())
        match self.active_tool:
            case "Circle Brush":
                self.canvas.configure(cursor="circle")
                self.transform_controls.grid_remove()  # Hide controls
                self.transform_active = False
                self.transform_tags.clear()

            case "Rectangle Tool":
                self.canvas.configure(cursor="tcross")
                self.transform_controls.grid_remove()  # Hide controls
                self.transform_active = False
                self.transform_tags.clear()

            case "Fill Tool":
                self.canvas.configure(cursor="spraycan")
                self.transform_controls.grid_remove()  # Hide controls
                self.transform_active = False
                self.transform_tags.clear()

            case "Text Tool":
                self.canvas.configure(cursor="xterm")
                self.transform_controls.grid_remove()  # Hide controls
                self.transform_active = False
                self.transform_tags.clear()

            case "Transform Tool":
                self.canvas.configure(cursor="fleur")
                # Show transform controls
                self.transform_controls.grid(
                    row=0, column=0, columnspan=3, sticky="ew", pady=(0, 5)
                )
                # Initialize transform state
                self.transform_mode = "move"
                self.move_btn.configure(fg_color="#4477AA")
                self.scale_btn.configure(fg_color="transparent")

            case "Delete Tool":
                self.canvas.configure(cursor="X_cursor")
                self.transform_controls.grid_remove()  # Hide controls
                self.transform_active = False
                self.transform_tags.clear()

            case "Image Tool":
                self.canvas.configure(cursor="plus")
                self.transform_controls.grid_remove()  # Hide controls
                self.transform_active = False
                self.transform_tags.clear()

    def open_text_entry_window(self):
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
    # Canvas Mouse Events
    ################################

    def mouse_move(self, event):
        self.canvas.delete("temp_bbox")
        if self.mouse_down:
            self.mouse_active_coords["previous"] = self.mouse_active_coords["current"]
            self.mouse_active_coords["current"] = (event.x, event.y)

            if (
                self.mouse_active_coords["previous"]
                != self.mouse_active_coords["current"]
                and self.mouse_active_coords["previous"] is not None
            ):
                match self.active_tool:
                    case "Circle Brush":
                        # Get stroke tag only once when starting a new stroke
                        if not hasattr(self, "current_brush_tag"):
                            self.current_brush_tag = self.get_stroke_tag(
                                self.active_tool
                            )
                            self.add_layer_to_panel(self.current_brush_tag)

                        self.canvas.create_line(
                            self.mouse_active_coords["previous"][0],
                            self.mouse_active_coords["previous"][1],
                            self.mouse_active_coords["current"][0],
                            self.mouse_active_coords["current"][1],
                            fill=self.hex_color,
                            width=self.element_size,
                            capstyle=tkinter.ROUND,
                            smooth=True,
                            splinesteps=36,
                            tags=self.current_brush_tag,
                        )
                    case "Rectangle Tool":
                        self.temp_rect = None
                        if self.mouse_down:
                            self.canvas.delete("temp_rect")
                            self.temp_rect = self.canvas.create_rectangle(
                                self.mouse_down_canvas_coords[0],
                                self.mouse_down_canvas_coords[1],
                                event.x,
                                event.y,
                                width=self.element_size,
                                fill=str(self.hex_color),
                                tags="temp_rect",
                            )
                    case "Transform Tool":
                        if self.transform_active:
                            match self.transform_mode:
                                case "move":
                                    dx = event.x - self.mouse_down_canvas_coords[0]
                                    dy = event.y - self.mouse_down_canvas_coords[1]
                                    for tag in self.transform_tags:
                                        self.canvas.move(tag, dx, dy)
                                    self.canvas.move("temp_bbox", dx, dy)

                                case "scale":
                                    for tag in self.transform_tags:
                                        bbox = self.canvas.bbox(tag)
                                        if bbox:
                                            center_x = (bbox[0] + bbox[2]) / 2
                                            center_y = (bbox[1] + bbox[3]) / 2

                                            # Calculate distance from center
                                            current_dist = math.sqrt(
                                                (event.x - center_x) ** 2
                                                + (event.y - center_y) ** 2
                                            )
                                            start_dist = math.sqrt(
                                                (
                                                    self.mouse_down_canvas_coords[0]
                                                    - center_x
                                                )
                                                ** 2
                                                + (
                                                    self.mouse_down_canvas_coords[1]
                                                    - center_y
                                                )
                                                ** 2
                                            )

                                            if start_dist > 0:
                                                scale = current_dist / start_dist
                                                scale = max(0.1, min(scale, 5.0))
                                                self.canvas.scale(
                                                    tag,
                                                    center_x,
                                                    center_y,
                                                    scale,
                                                    scale,
                                                )

                                                # Update bounding box
                                                self.canvas.delete("temp_bbox")
                                                new_bbox = self.canvas.bbox(tag)
                                                if new_bbox:
                                                    self.canvas.create_rectangle(
                                                        new_bbox[0] - 20,
                                                        new_bbox[1] - 20,
                                                        new_bbox[2] + 20,
                                                        new_bbox[3] + 20,
                                                        outline="#555555",
                                                        width=5,
                                                        tags="temp_bbox",
                                                    )

                            self.mouse_down_canvas_coords = (event.x, event.y)
                        else:
                            self.update_temp_bbox(event)
        else:
            match self.active_tool:
                case "Delete Tool":
                    self.update_temp_bbox(event)
                case "Transform Tool":
                    self.update_temp_bbox(event)

    def update_temp_bbox(self, event):
        self.canvas.delete("temp_bbox")
        item = self.canvas.find_closest(event.x, event.y)
        if item:
            tag = self.canvas.gettags(item[0])
            if tag:
                self.active_bbox = self.canvas.bbox(tag[0])
                if self.active_tool == "Delete Tool":
                    outline_color = "#FF5555"  # Slightly red color
                else:
                    outline_color = "#555555"
                self.canvas.create_rectangle(
                    self.active_bbox[0] - 20,
                    self.active_bbox[1] - 20,
                    self.active_bbox[2] + 20,
                    self.active_bbox[3] + 20,
                    outline=outline_color,
                    width=5,
                    tags="temp_bbox",
                )

    def canvas_mouse_down(self, event):
        self.mouse_down = True
        self.mouse_down_canvas_coords = (event.x, event.y)
        # Initialize current position for brush strokes
        self.mouse_active_coords["current"] = (event.x, event.y)
        match self.active_tool:
            case "Transform Tool":
                item = self.canvas.find_closest(event.x, event.y)[0]
                tag = self.canvas.gettags(item)
                if not self.transform_active:
                    self.transform_active = True
                    self.transform_tags = [tag[0]]
                    # Show bounding box for selected stroke
                    self.canvas.delete("temp_bbox")
                    bbox = self.canvas.bbox(tag[0])
                    if bbox:
                        self.canvas.create_rectangle(
                            bbox[0] - 20,
                            bbox[1] - 20,
                            bbox[2] + 20,
                            bbox[3] + 20,
                            outline="#555555",
                            width=5,
                            tags="temp_bbox",
                        )
                elif tag[0] not in self.transform_tags:
                    self.transform_active = False
                    self.transform_tags.clear()

    def canvas_mouse_release(self, event):
        self.mouse_down = False
        self.mouse_active_coords["previous"] = None
        self.mouse_active_coords["current"] = None
        self.mouse_release_canvas_coords = (event.x, event.y)

        # Clear brush tag when stroke is complete
        if hasattr(self, "current_brush_tag"):
            delattr(self, "current_brush_tag")

        match self.active_tool:
            case "Circle Brush":
                pass
            case "Rectangle Tool":
                self.canvas.delete("temp_rect")
                stroke_tag = self.get_stroke_tag(self.active_tool)
                self.canvas.create_rectangle(
                    self.mouse_down_canvas_coords[0],
                    self.mouse_down_canvas_coords[1],
                    self.mouse_release_canvas_coords[0],
                    self.mouse_release_canvas_coords[1],
                    width=self.element_size,
                    fill=str(self.hex_color),
                    outline=str(self.hex_color),
                    tags=stroke_tag,
                )
                self.add_layer_to_panel(stroke_tag)
            case "Text Tool":
                self.open_text_entry_window()
            case "Delete Tool":
                self.canvas.delete("temp_bbox")
                item = self.canvas.find_closest(event.x, event.y)[0]
                tag = self.canvas.gettags(item)
                if tag and "_" in tag[0]:  # Check for any valid element tag
                    self.delete_layer(tag[0])
            case "Image Tool":
                file_path = filedialog.askopenfilename(
                    filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff")]
                )
                if file_path:
                    self.place_image(file_path, event.x, event.y)
            case "Fill Tool":
                stroke_tag = self.get_stroke_tag(self.active_tool)
                self.canvas.create_rectangle(
                    0,
                    0,
                    self.canvas.winfo_width(),
                    self.canvas.winfo_height(),
                    fill=self.hex_color,
                    tags=stroke_tag,
                )
                self.add_layer_to_panel(stroke_tag)

    ################################
    # Layer Window
    ################################
    def add_layer_to_panel(self, stroke_tag):
        layer_frame = customtkinter.CTkFrame(self.layer_container)
        layer_frame.grid(
            row=len(self.layer_buttons), column=0, pady=2, padx=5, sticky="nsw"
        )
        layer_frame.grid_columnconfigure(0, weight=1)

        # Create more descriptive label
        tool_type, number = stroke_tag.split("_")
        label_text = f"{tool_type.capitalize()} {number}"

        # Make the label clickable and highlight on hover
        layer_label = customtkinter.CTkLabel(
            layer_frame,
            text=label_text,
            cursor="hand2",
        )
        layer_label.grid(row=0, column=0, pady=2, padx=5, sticky="w")

        # Bind click event to select the stroke
        layer_label.bind("<Button-1>", lambda e, tag=stroke_tag: self.select_layer(tag))

        # Dictionary to store buttons for managing references
        buttons = {}
        next_column = 1

        # Handle color edit button
        if tool_type in ["brush", "rect", "fill", "text"]:
            edit_button = customtkinter.CTkButton(
                layer_frame,
                text="",
                width=24,
                height=24,
                image=self.edit_icon,
                command=lambda t=stroke_tag: self.edit_layer_color(t),
            )
            edit_button.grid(row=0, column=next_column, pady=2, padx=2)
            buttons["edit_button"] = edit_button
            next_column += 1

        # Add text edit button only for text elements
        if tool_type == "text":
            edit_text_button = customtkinter.CTkButton(
                layer_frame,
                text="Edit Text",
                width=60,
                height=24,
                command=lambda t=stroke_tag: self.edit_layer_text(t),
            )
            edit_text_button.grid(row=0, column=next_column, pady=2, padx=2)
            buttons["edit_text_button"] = edit_text_button
            next_column += 1

        # Delete button with icon
        delete_button = customtkinter.CTkButton(
            layer_frame,
            text="",
            width=24,
            height=24,
            image=self.trash_icon,
            command=lambda t=stroke_tag: self.delete_layer(t),
        )
        delete_button.grid(row=0, column=next_column, pady=2, padx=2)
        buttons["delete_button"] = delete_button

        # Store all components in the layer_buttons dictionary
        self.layer_buttons[stroke_tag] = {
            "frame": layer_frame,
            "label": layer_label,
            **buttons,  # Unpack the buttons dictionary
        }

    def delete_layer(self, stroke_tag):
        """Delete a layer and update counters"""
        # Delete the stroke from canvas
        self.canvas.delete(stroke_tag)

        # Update the counter for the tool type
        tool_type, number = stroke_tag.split("_")
        if tool_type in self.tool_counters:
            self.tool_counters[tool_type] = max(
                self.tool_counters[tool_type], int(number)
            )

        # Delete the UI components
        if stroke_tag in self.layer_buttons:
            layer_info = self.layer_buttons[stroke_tag]
            layer_info["frame"].destroy()
            del self.layer_buttons[stroke_tag]
            self._reposition_layers()

    def _reposition_layers(self):
        for idx, (tag, layer_info) in enumerate(self.layer_buttons.items()):
            layer_info["frame"].grid(row=idx, column=0, pady=2, padx=5, sticky="ew")

    def select_layer(self, stroke_tag):
        # Check if layer is already selected
        if hasattr(self, "selected_layer") and self.selected_layer == stroke_tag:
            # Layer is already selected, show color picker
            color_code = colorchooser.askcolor(
                title="Choose stroke color",
                color=self.canvas.itemcget(stroke_tag, "fill"),
            )
            if color_code:
                # Update the stroke color
                if "brush" in stroke_tag or "rect" in stroke_tag:
                    self.canvas.itemconfig(stroke_tag, fill=color_code[1])
                    if "rect" in stroke_tag:
                        self.canvas.itemconfig(stroke_tag, outline=color_code[1])
                elif "text" in stroke_tag:
                    self.canvas.itemconfig(stroke_tag, fill=color_code[1])
                elif "fill" in stroke_tag:
                    self.canvas.itemconfig(stroke_tag, fill=color_code[1])
        else:
            # Reset previous selections
            for layer_info in self.layer_buttons.values():
                layer_info["frame"].configure(fg_color=("gray86", "gray17"))
                layer_info["label"].configure(fg_color=("gray86", "gray17"))

            # Highlight selected layer
            self.layer_buttons[stroke_tag]["frame"].configure(
                fg_color=("#4477AA", "#4477AA")
            )
            self.layer_buttons[stroke_tag]["label"].configure(
                fg_color=("#4477AA", "#4477AA")
            )

            # Set transform tool as active
            self.radio_tool_var.set(4)  # Index for Transform Tool
            self.transform_active = True
            self.transform_tags = [stroke_tag]
            self.selected_layer = stroke_tag

            # Show bounding box for selected stroke
            self.canvas.delete("temp_bbox")
            bbox = self.canvas.bbox(stroke_tag)
            if bbox:
                self.canvas.create_rectangle(
                    bbox[0] - 20,
                    bbox[1] - 20,
                    bbox[2] + 20,
                    bbox[3] + 20,
                    outline="#555555",
                    width=5,
                    tags="temp_bbox",
                )

    def edit_layer_color(self, stroke_tag):
        """Edit the color of a layer"""
        color_code = colorchooser.askcolor(
            title="Choose stroke color",
            color=self.canvas.itemcget(stroke_tag, "fill"),
        )
        if color_code:
            # Update the stroke color based on type
            if "brush" in stroke_tag or "rect" in stroke_tag:
                self.canvas.itemconfig(stroke_tag, fill=color_code[1])
                if "rect" in stroke_tag:
                    self.canvas.itemconfig(stroke_tag, outline=color_code[1])
            elif "text" in stroke_tag:
                self.canvas.itemconfig(stroke_tag, fill=color_code[1])
            elif "fill" in stroke_tag:
                self.canvas.itemconfig(stroke_tag, fill=color_code[1])

    def edit_layer_text(self, stroke_tag):
        """Change the font size of a text element"""
        try:
            # Get current text
            current_text = self.canvas.itemcget(stroke_tag, "text")

            # Create new font with current element_size
            new_font = customtkinter.CTkFont(size=self.element_size)

            # Update the text element's font
            self.canvas.itemconfig(stroke_tag, font=new_font)

            # Update bounding box if transform tool is active
            if self.transform_active and stroke_tag in self.transform_tags:
                self.canvas.delete("temp_bbox")
                bbox = self.canvas.bbox(stroke_tag)
                if bbox:
                    self.canvas.create_rectangle(
                        bbox[0] - 20,
                        bbox[1] - 20,
                        bbox[2] + 20,
                        bbox[3] + 20,
                        outline="#555555",
                        width=5,
                        tags="temp_bbox",
                    )

        except Exception as e:
            print(f"Error updating text size: {e}")

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
        available_ports = []
        for i in range(4):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    available_ports.append(i)
                cap.release()
        return available_ports

    def change_camera(self, selection):
        if self.camera_running:
            self.close_camera()
        camera_index = int(selection.replace("Camera ", ""))
        self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)

    def toggle_camera_flip(self):
        self.flip_camera_enabled = self.flip_camera.get()

    def open_camera(self):
        if not self.camera_running:
            if self.cap is None or not self.cap.isOpened():
                # Try to open the currently selected camera
                selected_camera = self.camera_select.get()
                camera_index = int(selected_camera.replace("Camera ", ""))
                self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)

                if not self.cap.isOpened():
                    print(f"Failed to open camera {camera_index}")
                    return

            self.camera_running = True
            self.stop_event.clear()
            self.camera_thread = threading.Thread(target=self._camera_loop)
            self.camera_thread.start()
            self.open_camera_btn.configure(state="disabled")
            self.close_camera_btn.configure(state="normal")
            self.webcam_image_label.configure(text="")

    def _camera_loop(self):
        mouse_pressed = False
        process_this_frame = True  # Add frame skip counter

        while (
            self.camera_running
            and self.cap is not None
            and self.cap.isOpened()
            and not self.stop_event.is_set()
        ):
            start_time = time.time()
            ret, frame = self.cap.read()
            if not ret:
                break

            # Process every other frame
            if process_this_frame:
                # Resize frame for faster processing
                small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)

                if hasattr(self, "flip_camera_enabled") and self.flip_camera_enabled:
                    small_frame = cv2.flip(small_frame, 1)

                # Convert and process
                opencv_image = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                results = self.hands.process(opencv_image)

                # Scale back up for display
                opencv_image = cv2.resize(
                    opencv_image, (self.frame_width, self.frame_height)
                )
            else:
                # Just flip if needed without processing
                if hasattr(self, "flip_camera_enabled") and self.flip_camera_enabled:
                    frame = cv2.flip(frame, 1)
                opencv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            current_click = False

            # Get bounds
            left_bound = self.left_bound_scroller.get()
            right_bound = self.right_bound_scroller.get()
            top_bound = self.top_bound_scroller.get()
            bottom_bound = self.bottom_bound_scroller.get()

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
                    self.mp_hands.HandLandmark.INDEX_FINGER_TIP
                ]
                thumb_tip_landmark = hand_landmarks.landmark[
                    self.mp_hands.HandLandmark.THUMB_TIP
                ]
                palm_landmark = hand_landmarks.landmark[
                    self.mp_hands.HandLandmark.WRIST
                ]
                distance = math.hypot(
                    index_tip_landmark.x - thumb_tip_landmark.x,
                    index_tip_landmark.y - thumb_tip_landmark.y,
                )
                cv2.putText(
                    opencv_image,
                    "Distance: " + str(distance)[:6],
                    (30, 50),
                    1,
                    2,
                    (255, 255, 100),
                    2,
                )

                if distance < 0.05:  # Threshold for "OK" gesture
                    current_click = True

                mouse_x = np.interp(
                    palm_landmark.x * self.frame_width,
                    [left_bound, right_bound],
                    [0, self.screen_width - 1],
                )
                mouse_y = np.interp(
                    palm_landmark.y * self.frame_height,
                    [top_bound, bottom_bound],
                    [0, self.screen_height - 1],
                )

                # Add the new positions to the deque
                self.mouse_x_positions.append(mouse_x)
                self.mouse_y_positions.append(mouse_y)

                # Calculate the average positions
                smoothed_mouse_x = sum(self.mouse_x_positions) / len(
                    self.mouse_x_positions
                )
                smoothed_mouse_y = sum(self.mouse_y_positions) / len(
                    self.mouse_y_positions
                )

                if (
                    hasattr(self, "mouse_control_enabled")
                    and self.mouse_control_enabled
                ):
                    pyautogui.moveTo(int(smoothed_mouse_x), int(smoothed_mouse_y))

                self.mp_drawing.draw_landmarks(
                    opencv_image, hand_landmarks, self.mp_hands.HAND_CONNECTIONS
                )

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
            label_width = self.webcam_image_label.winfo_width()
            label_height = self.webcam_image_label.winfo_height()

            # Ensure minimum dimensions
            display_width = max(int(self.frame_width * 0.6), 800)
            display_height = max(
                int(self.frame_height * 0.6), 450
            )  # Maintains 16:9 aspect ratio

            # Create scaled CTkImage
            captured_image = Image.fromarray(opencv_image)
            photo_image = customtkinter.CTkImage(
                light_image=captured_image,
                dark_image=captured_image,
                size=(display_width, display_height),
            )

            # Update the label with the new image
            self.webcam_image_label.configure(image=photo_image)
            self.webcam_image_label.photo_image = photo_image

            # Limit the frame rate to 30 FPS
            elapsed_time = time.time() - start_time
            time.sleep(max(0, 1 / 30 - elapsed_time))

        self.close_camera()

    def close_camera(self):
        """Safely close the camera and cleanup resources"""
        # Stop camera first
        self.camera_running = False
        self.stop_event.set()

        # Release camera resources
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        cv2.destroyAllWindows()

        # Ensure we're in the main thread for UI updates
        def update_ui():
            if hasattr(self, "webcam_image_label"):
                try:
                    self.webcam_image_label.destroy()
                    self.webcam_image_label = customtkinter.CTkLabel(
                        self.tabview.tab("Webcam Image"), text="Webcam Image"
                    )
                    self.webcam_image_label.grid(row=4, column=0, columnspan=4)
                    self.open_camera_btn.configure(state="normal")
                    self.close_camera_btn.configure(state="disabled")
                except Exception as e:
                    print(f"Error updating UI: {e}")

        # Schedule UI update for next mainloop iteration
        self.after(100, update_ui)

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

    def translate(value, leftMin, leftMax, rightMin, rightMax):
        # Figure out how 'wide' each range is
        leftSpan = leftMax - leftMin
        rightSpan = rightMax - rightMin

        # Convert the left range into a 0-1 range (float)
        valueScaled = float(value - leftMin) / float(leftSpan)

        # Convert the 0-1 range into a value in the right range.
        return rightMin + (valueScaled * rightSpan)

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
        }
        prefix = tool_prefix.get(tool_name, "element")
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

            # Maintain aspect ratio (16:9)
            aspect_ratio = 16 / 9

            # Calculate new dimensions maintaining aspect ratio
            if frame_width / frame_height > aspect_ratio:
                # Width is too wide, constrain by height
                new_height = frame_height
                new_width = int(new_height * aspect_ratio)
            else:
                # Height is too tall, constrain by width
                new_width = frame_width
                new_height = int(new_width / aspect_ratio)

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
