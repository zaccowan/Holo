import os
import tkinter
import tkinter.messagebox
import tkinter.ttk
import customtkinter
from tkinter import colorchooser, filedialog
from PIL import ImageGrab, Image, ImageTk
import ctypes
import numpy as np
import cv2

import math
import pyautogui
import mediapipe as mp
import threading

import vosk
import pyaudio
import json


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

    cap = cv2.VideoCapture(0)
    frame_width, frame_height = 1280, 720
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)

    def __init__(self):
        super().__init__()

        # configure window
        self.title("Holo")
        self.geometry(f"{1280}x{720}")
        self.bind("<Escape>", lambda e: app.quit())

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

        self.canvas.bind("<Button-1>", self.canvas_mouse_down)
        self.canvas.bind("<ButtonRelease-1>", self.canvas_mouse_release)
        self.canvas.bind("<Motion>", self.mouse_move)

        # Generated AI Image Tab

        # Webcam Tab
        self.tabview.tab("Webcam Image").columnconfigure((0, 1), weight=1)
        self.tabview.tab("Webcam Image").rowconfigure(2, weight=1)
        self.width_offset_scroller = customtkinter.CTkSlider(
            self.tabview.tab("Webcam Image"),
            command=self.set_element_size,
            progress_color="#4477AA",
            from_=0,
            to=int(self.screen_width / 2),
        )
        self.width_offset_scroller.grid(row=0, column=0, padx=20)
        self.height_offset_scroller = customtkinter.CTkSlider(
            self.tabview.tab("Webcam Image"),
            command=self.set_element_size,
            progress_color="#4477AA",
            from_=0,
            to=int(self.screen_height / 2),
        )
        self.height_offset_scroller.grid(row=0, column=1, padx=20)

        self.webcam_image_label = customtkinter.CTkLabel(
            self.tabview.tab("Webcam Image"), text="Webcam Image"
        )
        self.webcam_image_label.grid(row=2, column=0, columnspan=2)
        self.open_camera_btn = customtkinter.CTkButton(
            self.tabview.tab("Webcam Image"),
            text="Open Camera",
            command=self.open_camera,
        )
        self.open_camera_btn.grid(row=3, column=0)
        self.close_camera_btn = customtkinter.CTkButton(
            self.tabview.tab("Webcam Image"),
            text="Close Camera",
            state="disabled",
            command=self.close_camera,
        )
        self.close_camera_btn.grid(row=3, column=1)

        # ################################
        # ################################
        # # create main entry and button
        # ################################
        # ################################
        self.prompt_entry = customtkinter.CTkEntry(
            self.tabview.tab("Canvas"),
            placeholder_text="Prompt to guide image generation...",
        )
        self.prompt_entry.grid(
            row=1, column=0, padx=(20, 20), pady=(10, 10), sticky="ew"
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
            row=1, column=1, padx=(20, 20), pady=(20, 20), sticky="ew"
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
            row=1, column=2, padx=(20, 20), pady=(20, 20), sticky="ew"
        )

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

        if self.mouse_down:
            self.mouse_active_coords["previous"] = self.mouse_active_coords["current"]
            self.mouse_active_coords["current"] = (event.x, event.y)
            # print(self.mouse_active_coords)
            if (
                self.mouse_active_coords["previous"]
                != self.mouse_active_coords["current"]
                and self.mouse_active_coords["previous"] != None
            ):
                x_interp_float = np.linspace(
                    self.mouse_active_coords["previous"][0],
                    self.mouse_active_coords["current"][0],
                    num=150 - self.element_size,
                )
                y_interp_float = np.linspace(
                    self.mouse_active_coords["previous"][1],
                    self.mouse_active_coords["current"][1],
                    num=150 - self.element_size,
                )
                x_interp = [int(x) for x in x_interp_float]
                y_interp = [int(y) for y in y_interp_float]

                match self.active_tool:
                    case "Circle Brush":
                        for index, x in enumerate(x_interp):
                            self.canvas.create_aa_circle(
                                x,
                                y_interp[index],
                                self.element_size,
                                0,
                                str(self.hex_color),
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
                        for tag in self.transform_tags:
                            self.canvas.moveto(tag, event.x, event.y)
        else:
            match self.active_tool:
                case "Delete Tool":
                    self.canvas.delete("temp_bbox")
                    item = self.canvas.find_closest(event.x, event.y)[0]
                    tag = self.canvas.gettags(item)
                    print(tag)
                    if self.active_bbox is None:
                        self.active_bbox = self.canvas.bbox(tag[0])
                        self.canvas.create_rectangle(
                            self.active_bbox[0] - 20,
                            self.active_bbox[1] - 20,
                            self.active_bbox[2] + 20,
                            self.active_bbox[3] + 20,
                            outline="#555555",
                            width=5,
                            tags="temp_bbox",
                        )
                    elif self.active_bbox is not self.canvas.bbox(tag[0]):
                        self.active_bbox = self.canvas.bbox(tag[0])
                        self.canvas.create_rectangle(
                            self.active_bbox[0] - 20,
                            self.active_bbox[1] - 20,
                            self.active_bbox[2] + 20,
                            self.active_bbox[3] + 20,
                            outline="#555555",
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
                if self.transform_active:
                    self.transform_active = False
                    self.transform_tags.clear()
                else:
                    self.transform_active = True
                    item = self.canvas.find_closest(event.x, event.y)[0]
                    tag = self.canvas.gettags(item)
                    self.transform_tags.append(tag[0])
        # print("Mouse Down:", self.mouse_down_canvas_coords)

    def canvas_mouse_release(self, event):
        self.mouse_down = False
        self.mouse_active_coords["previous"] = None
        self.mouse_active_coords["current"] = None
        self.mouse_release_canvas_coords = (event.x, event.y)

        match self.active_tool:
            case "Circle Brush":
                self.canvas.create_aa_circle(
                    event.x,
                    event.y,
                    self.element_size,
                    0,
                    str(self.hex_color),
                    tags="brush_stroke" + str(self.stroke_counter),
                )
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
            case "Text Tool":
                self.open_text_entry_window()
            case "Delete Tool":
                self.canvas.delete("temp_bbox")
                item = self.canvas.find_closest(event.x, event.y)[0]
                tag = self.canvas.gettags(item)
                self.canvas.delete(tag[0])
        # print("Mouse Release:", self.mouse_release_canvas_coords)

    ################################
    # Canvas Saving and AI Generation
    ################################
    def generate_ai_image(self):
        pass

    def canvas_save_png(self):
        file_path = filedialog.asksaveasfilename(
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
                self.canvas.winfo_rootx() + self.canvas.winfo_width(),
                self.canvas.winfo_rooty() + self.canvas.winfo_height(),
            )
        ).save(file_path)

    ################################
    # Webcam Functions
    ################################

    def open_camera(self):

        if self.cap.isOpened():
            self.open_camera_btn.configure(state="disabled")
            self.close_camera_btn.configure(state="normal")

        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            self.open_camera

        # Capture the video frame by frame
        _, frame = self.cap.read()

        frame = cv2.flip(frame, 1)

        # Convert image from one color space to other
        opencv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = self.hands.process(opencv_image)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # print(hand_landmarks.landmark[0])

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

                pyautogui.moveTo(
                    palm_landmark.x * self.screen_width,
                    palm_landmark.y * self.screen_height,
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

                # Click detection (adjust threshold as needed)
                if distance < 0.05:
                    current_click = True

                cv2.circle(
                    opencv_image,
                    (
                        int(
                            self.getPixelPos(index_tip_landmark.x, self.frame_width)
                            - 10
                        ),
                        int(
                            self.getPixelPos(index_tip_landmark.y, self.frame_height)
                            - 10
                        ),
                    ),
                    10,
                    (0, 0, 255),
                    -1,
                )

                # Draw hand landmarks (optional)
                self.mp_drawing.draw_landmarks(
                    opencv_image, hand_landmarks, self.mp_hands.HAND_CONNECTIONS
                )
                break

        # Capture the latest frame and transform to image
        captured_image = Image.fromarray(opencv_image)

        # Convert captured image to photoimage
        photo_image = ImageTk.PhotoImage(image=captured_image)

        self.webcam_image_label.configure(text="")

        # Displaying photoimage in the label
        self.webcam_image_label.photo_image = photo_image

        # Configure image in the label
        self.webcam_image_label.configure(image=ImageTk.PhotoImage(captured_image))

        # Repeat the same process after every 10 seconds
        self.webcam_image_label.after(10, self.open_camera)

    def close_camera(self):
        self.open_camera_btn.configure(state="normal")
        self.close_camera_btn.configure(state="disabled")
        self.cap.release()
        cv2.destroyAllWindows()
        self.webcam_image_label.destroy()
        self.webcam_image_label = customtkinter.CTkLabel(
            self.tabview.tab("Webcam Image"), text="Webcam Image"
        )
        self.webcam_image_label.grid(row=2, column=0, columnspan=2)
        self.webcam_image_label.configure(image=None)
        self.webcam_image_label.configure(text="Webcam Image")

    ################################
    # Helper functions
    ################################
    def getPixelPos(self, floatCoord, frameDim):
        return floatCoord * frameDim


if __name__ == "__main__":
    app = Holo()
    app.mainloop()
