# Imports for GUI library and styling system
import os
import sys
import tkinter
import tkinter.messagebox
import tkinter.ttk
import customtkinter
from tkinter import colorchooser, filedialog
from PIL import ImageGrab, Image, ImageTk
import ctypes
import time
import collections

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
import base64


customtkinter.set_appearance_mode(
    "System"
)  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme(
    "dark-blue"
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

    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
    )

    canvas_text = None

    screen_width, screen_height = pyautogui.size()
    pyautogui.FAILSAFE = False

    current_click = True

    def __init__(self):
        super().__init__()

        self.cap = None  # Initialize as None instead of with specific index
        self.frame_width, self.frame_height = 1280, 720

        self.camera_thread = None
        self.camera_running = False
        self.stop_event = threading.Event()

        # Smoothing parameters
        self.smoothing_window_size = 5
        self.mouse_x_positions = collections.deque(maxlen=self.smoothing_window_size)
        self.mouse_y_positions = collections.deque(maxlen=self.smoothing_window_size)

        # configure window
        self.title("Holo")
        self.geometry(f"{1280}x{720}")
        self.bind("<Escape>", lambda e: app.quit())

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
        self.canvas = customtkinter.CTkCanvas(
            self.tabview.tab("Canvas"),
            width=1280,
            height=720,
            bg="white",
            cursor="circle",
        )

        self.tabview.tab("Canvas").grid_columnconfigure((0, 1, 2), weight=1)
        self.tabview.tab("Canvas").grid_rowconfigure(0, weight=1)
        self.canvas.grid(row=0, column=0, columnspan=3)

        # Canvas Mouse Events
        self.canvas.bind("<Button-1>", self.canvas_mouse_down)
        self.canvas.bind("<ButtonRelease-1>", self.canvas_mouse_release)
        self.canvas.bind("<Motion>", self.mouse_move)

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
            self.tabview.tab("Canvas"), width=200, corner_radius=0
        )
        self.layer_panel.grid(row=0, column=3, rowspan=3, sticky="nsew", padx=5, pady=5)
        self.layer_panel.grid_columnconfigure(0, weight=1)

        # Add layer panel label
        self.layer_panel_label = customtkinter.CTkLabel(
            self.layer_panel,
            text="Layers",
            font=customtkinter.CTkFont(size=16, weight="bold"),
        )
        self.layer_panel_label.grid(row=0, column=0, pady=5, padx=5)

        # Add scrollable frame for layers
        self.layer_container = customtkinter.CTkScrollableFrame(
            self.layer_panel, width=180, height=600
        )
        self.layer_container.grid(row=1, column=0, pady=5, padx=5, sticky="nsew")

        # Dictionary to store layer buttons
        self.layer_buttons = {}

        # Generated AI Image Tab
        self.tabview.tab("Genrated AI Image").columnconfigure(0, weight=1)
        self.tabview.tab("Genrated AI Image").rowconfigure(0, weight=1)
        self.gen_ai_image_label = customtkinter.CTkLabel(
            self.tabview.tab("Genrated AI Image"),
            text="Waiting for AI Generated Image (this may take time)",
        )
        self.gen_ai_image_label.grid(row=0, column=0)

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

        # Bounds control frame - right side
        self.bounds_frame = customtkinter.CTkFrame(self.tabview.tab("Webcam Image"))
        self.bounds_frame.grid(row=0, column=2, columnspan=2, padx=5, pady=5)

        # X, Y position controls
        self.bound_pos_label = customtkinter.CTkLabel(
            self.bounds_frame, text="Bounding Box Position (X, Y):"
        )
        self.bound_pos_label.grid(row=0, column=0, columnspan=2, padx=5, pady=2)

        self.x_center_scroller = customtkinter.CTkSlider(
            self.bounds_frame,
            width=200,
            command=self.set_element_size,
            progress_color="#4477AA",
            from_=0,
            to=int(self.frame_width),
        )
        self.x_center_scroller.grid(row=1, column=0, padx=5, pady=2)

        self.y_center_scroller = customtkinter.CTkSlider(
            self.bounds_frame,
            width=200,
            command=self.set_element_size,
            progress_color="#4477AA",
            from_=0,
            to=int(self.frame_height),
        )
        self.y_center_scroller.grid(row=1, column=1, padx=5, pady=2)

        # Size controls
        self.bound_size_label = customtkinter.CTkLabel(
            self.bounds_frame, text="Bounding Box Size (Width, Height):"
        )
        self.bound_size_label.grid(row=2, column=0, columnspan=2, padx=5, pady=2)

        self.bound_width_scroller = customtkinter.CTkSlider(
            self.bounds_frame,
            width=200,
            command=self.set_element_size,
            progress_color="#4477AA",
            from_=0,
            to=int(self.frame_width * 2),
        )
        self.bound_width_scroller.grid(row=3, column=0, padx=5, pady=2)

        self.bound_height_scroller = customtkinter.CTkSlider(
            self.bounds_frame,
            width=200,
            command=self.set_element_size,
            progress_color="#4477AA",
            from_=0,
            to=int(self.frame_height * 2),
        )
        self.bound_height_scroller.grid(row=3, column=1, padx=5, pady=2)

        # Camera view
        self.webcam_image_label = customtkinter.CTkLabel(
            self.tabview.tab("Webcam Image"), text="Webcam Image"
        )
        self.webcam_image_label.grid(row=4, column=0, columnspan=4, sticky="nsew")

        # Camera control buttons - reversed order
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
        self.close_camera_btn.grid(row=5, column=3, padx=5, pady=5)

        # ################################
        # ################################
        # # create main entry and button
        # ################################
        # ################################

        # set default values
        self.appearance_mode_optionemenu.set("Dark")
        self.scaling_optionemenu.set("100%")

    ########################################################################################################################################################
    ########################################################################################################################################################
    # End of init ##########################################################################################################################################
    ########################################################################################################################################################
    ########################################################################################################################################################

    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

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
            case "Rectangle Tool":
                self.canvas.configure(cursor="tcross")
            case "Fill Tool":
                self.canvas.configure(cursor="spraycan")
            case "Text Tool":
                self.canvas.configure(cursor="xterm")
            case "Transform Tool":
                self.canvas.configure(cursor="fleur")
            case "Delete Tool":
                self.canvas.configure(cursor="X_cursor")

        # print(self.active_tool)

    def open_text_entry_window(self):
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = TextEntryWindow(
                self
            )  # create window if its None or destroyed
        else:
            self.toplevel_window.focus()  # if window exists focus it

        # if self.canvas_text is not None:
        #     print(self.canvas_text)

    def set_canvas_text(self, entry_text):
        self.canvas_text = entry_text
        self.canvas.create_text(
            self.mouse_release_canvas_coords[0],
            self.mouse_release_canvas_coords[1],
            text=entry_text,
            font=customtkinter.CTkFont(size=self.element_size),
        )
        # print(self.canvas_text)

    ################################
    # Canvas Mouse Events
    ################################

    def mouse_move(self, event):
        # Clear any temporary rectangles draw by delete or transform tool
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
                            tags="brush_stroke" + str(self.stroke_counter),
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
                            dx = event.x - self.mouse_down_canvas_coords[0]
                            dy = event.y - self.mouse_down_canvas_coords[1]
                            for tag in self.transform_tags:
                                self.canvas.move(tag, dx, dy)
                            self.canvas.move("temp_bbox", dx, dy)
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
        if self.active_tool != "Transform Tool":
            self.stroke_counter += 1
        self.mouse_down = True
        self.mouse_down_canvas_coords = (event.x, event.y)
        match self.active_tool:
            case "Fill Tool":
                self.canvas.create_rectangle(
                    0,
                    0,
                    self.canvas.winfo_width(),
                    self.canvas.winfo_height(),
                    fill=self.hex_color,
                    tags="brush_stroke" + str(self.stroke_counter),
                )
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

        match self.active_tool:
            case "Circle Brush":
                # Add the new stroke to the layer panel
                self.add_layer_to_panel(f"brush_stroke{self.stroke_counter}")
            case "Rectangle Tool":
                self.canvas.delete("temp_rect")
                self.canvas.create_rectangle(
                    self.mouse_down_canvas_coords[0],
                    self.mouse_down_canvas_coords[1],
                    self.mouse_release_canvas_coords[0],
                    self.mouse_release_canvas_coords[1],
                    width=self.element_size,
                    fill=str(self.hex_color),
                    outline=str(self.hex_color),
                    tags="brush_stroke" + str(self.stroke_counter),
                )
                # Add the new rectangle to the layer panel
                self.add_layer_to_panel(f"brush_stroke{self.stroke_counter}")
            case "Text Tool":
                self.open_text_entry_window()
            case "Delete Tool":
                self.canvas.delete("temp_bbox")
                item = self.canvas.find_closest(event.x, event.y)[0]
                tag = self.canvas.gettags(item)
                if tag and tag[0].startswith(
                    "brush_stroke"
                ):  # Ensure it's a brush stroke
                    self.delete_layer(tag[0])

    ################################
    # Layer Window
    ################################
    def add_layer_to_panel(self, stroke_tag):
        layer_frame = customtkinter.CTkFrame(self.layer_container)
        layer_frame.grid(
            row=len(self.layer_buttons), column=0, pady=2, padx=5, sticky="ew"
        )
        layer_frame.grid_columnconfigure(0, weight=1)

        # Make the label clickable and highlight on hover
        layer_label = customtkinter.CTkLabel(
            layer_frame,
            text=f"Stroke {stroke_tag.replace('brush_stroke', '')}",
            cursor="hand2",
        )
        layer_label.grid(row=0, column=0, pady=2, padx=5, sticky="w")

        # Bind click event to select the stroke
        layer_label.bind("<Button-1>", lambda e, tag=stroke_tag: self.select_layer(tag))

        delete_button = customtkinter.CTkButton(
            layer_frame,
            text="Delete",
            width=60,
            height=24,
            command=lambda t=stroke_tag: self.delete_layer(t),
        )
        delete_button.grid(row=0, column=1, pady=2, padx=5)

        self.layer_buttons[stroke_tag] = {
            "frame": layer_frame,
            "label": layer_label,
            "delete_button": delete_button,
        }

    def delete_layer(self, stroke_tag):
        self.canvas.delete(stroke_tag)
        self.layer_buttons[stroke_tag].destroy()
        del self.layer_buttons[stroke_tag]

    def select_layer(self, stroke_tag):
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
            for index, item in enumerate(output):
                with open(f"output_{index}.png", "wb") as file:
                    file.write(item.read())

            ai_gen_image = cv2.imread("output_0.png")
            ai_gen_image = Image.fromarray(ai_gen_image)
            ai_photo_image = ImageTk.PhotoImage(image=ai_gen_image)
            self.gen_ai_image_label.configure(text="")
            self.gen_ai_image_label.ai_photo_image = ai_photo_image
            self.gen_ai_image_label.configure(image=ai_photo_image)

        replicate_thread = threading.Thread(target=run_replicate)
        replicate_thread.start()
        # pass

    def canvas_save_png(self):
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
        """Test and return available camera indices"""
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
        """Change the active camera"""
        if self.camera_running:
            self.close_camera()
        camera_index = int(selection.replace("Camera ", ""))
        self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)

    def toggle_camera_flip(self):
        """Toggle camera flip state"""
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
        # Remove camera initialization from here since it's handled in open_camera
        mouse_pressed = False

        while (
            self.camera_running
            and self.cap is not None
            and self.cap.isOpened()
            and not self.stop_event.is_set()
        ):
            start_time = time.time()

            # Capture the video frame by frame
            ret, frame = self.cap.read()
            if not ret:
                break

            if hasattr(self, "flip_camera_enabled") and self.flip_camera_enabled:
                frame = cv2.flip(frame, 1)

            # frame = cv2.flip(frame, 1)
            # Convert image from one color space to other
            opencv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(opencv_image)
            current_click = False

            bounding_center_x = self.x_center_scroller.get()
            bounding_center_y = self.y_center_scroller.get()
            bounding_width = self.bound_width_scroller.get()
            bounding_height = self.bound_height_scroller.get()

            opencv_image = cv2.rectangle(
                opencv_image,
                (
                    int(bounding_center_x - (bounding_width / 2)),
                    int(bounding_center_y - (bounding_height / 2)),
                ),
                (
                    int(bounding_center_x + (bounding_width / 2)),
                    int(bounding_center_y + (bounding_height / 2)),
                ),
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
                    [
                        int(bounding_center_x - (bounding_width / 2)),
                        int(bounding_center_x + (bounding_width / 2)),
                    ],
                    [0, self.screen_width - 1],
                )
                mouse_y = np.interp(
                    palm_landmark.y * self.frame_height,
                    [
                        int(bounding_center_y - (bounding_height / 2)),
                        int(bounding_center_y + (bounding_height / 2)),
                    ],
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

            captured_image = Image.fromarray(opencv_image)
            photo_image = ImageTk.PhotoImage(image=captured_image)

            # Update the label with the new image
            self.webcam_image_label.configure(image=photo_image)
            self.webcam_image_label.photo_image = photo_image

            # Limit the frame rate to 30 FPS
            elapsed_time = time.time() - start_time
            time.sleep(max(0, 1 / 30 - elapsed_time))

        self.close_camera()

    def close_camera(self):
        self.camera_running = False
        self.stop_event.set()
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        cv2.destroyAllWindows()

        # Recreate the webcam label
        self.webcam_image_label.destroy()
        self.webcam_image_label = customtkinter.CTkLabel(
            self.tabview.tab("Webcam Image"), text="Webcam Image"
        )
        self.webcam_image_label.grid(row=4, column=0, columnspan=3, sticky="nsew")
        self.open_camera_btn.configure(state="normal")
        self.close_camera_btn.configure(state="disabled")

    def on_closing(self):
        self.close_camera()
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


if __name__ == "__main__":
    app = Holo()
    app.mainloop()
