import ctypes
import tkinter
import customtkinter
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

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


class BaseGUI(customtkinter.CTk):

    def __init__(
        self,
        parent,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.parent = parent
        self.parent.title("Holo")
        self.parent.geometry(f"{DEFAULT_FRAME_WIDTH}x{DEFAULT_FRAME_HEIGHT}")
        # set a minmum size for the window
        self.parent.minsize(1280, 720)

        # Optional: Add F11 key binding to toggle fullscreen
        self.parent.bind("<F11>", self.parent.toggle_fullscreen)
        self.parent.bind("<Escape>", lambda e: self.parent.on_closing())

        # Override the protocol method to detect window close
        self.parent.protocol("WM_DELETE_WINDOW", self.parent.on_closing)

        self.parent.toplevel_window = None

        self.parent.holo_logo = tkinter.PhotoImage(
            file=str(
                Path(__file__).parent.parent
                / "assets/images/holo_transparent_scaled.png"
            )
        )
        myappid = "Holo"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        self.parent.wm_iconbitmap(
            str(
                Path(__file__).parent.parent
                / "assets/images/holo_transparent_scaled.png"
            )
        )

        # configure grid layout (4x4)
        self.parent.grid_columnconfigure(1, weight=1)
        self.parent.grid_columnconfigure((2, 3), weight=0)
        self.parent.grid_rowconfigure((0, 1, 2), weight=1)

        ################################
        ################################
        # create sidebar frame with widgets
        ################################
        ################################
        self.parent.sidebar_frame = customtkinter.CTkFrame(
            self.parent, width=140, corner_radius=0
        )
        self.parent.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")

        self.parent.sidebar_frame.grid_rowconfigure(5, weight=1)

        self.parent.logo_label = customtkinter.CTkLabel(
            self.parent.sidebar_frame,
            text="Holo Tools",
            font=customtkinter.CTkFont(size=20, weight="bold"),
        )

        self.parent.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.parent.color_label = customtkinter.CTkLabel(
            self.parent.sidebar_frame,
            text=f"Element Color: {self.parent.hex_color}",
            fg_color=self.parent.hex_color,
            font=("Arial", 12),
            padx=20,
            pady=5,
            corner_radius=5,
            cursor="hand2",
        )
        self.parent.color_label.bind("<Button-1>", self.parent.choose_color)
        self.parent.color_label.grid(row=2, column=0, rowspan=2, padx=20, pady=(5, 50))

        self.parent.element_size_label = customtkinter.CTkLabel(
            self.parent.sidebar_frame,
            text=f"Element Size: {self.parent.element_size}",
            font=("Arial", 12),
            pady=10,
        )

        self.parent.element_size_label.grid(
            row=3,
            column=0,
            padx=(20, 10),
            pady=(10, 0),
            sticky="nsw",
        )
        self.parent.element_size_slider = customtkinter.CTkSlider(
            self.parent.sidebar_frame,
            from_=1,
            to=100,
            number_of_steps=100,
            command=self.parent.set_element_size,
            progress_color="#4477AA",
        )
        self.parent.element_size_slider.grid(
            row=4, column=0, padx=(20, 10), pady=(0, 10)
        )

        # create radiobutton frame
        self.parent.radiobutton_frame = customtkinter.CTkFrame(
            self.parent.sidebar_frame
        )
        self.parent.radiobutton_frame.grid(
            row=5, column=0, padx=(20, 20), pady=(20, 0), sticky="nsew"
        )
        self.parent.radio_tool_var = tkinter.IntVar(value=0)
        self.parent.radio_tool_var.trace_add(
            "write", callback=self.parent.set_active_tool
        )
        self.parent.label_radio_group = customtkinter.CTkLabel(
            master=self.parent.radiobutton_frame, text="Select Tool:"
        )
        self.parent.label_radio_group.grid(
            row=0, column=0, columnspan=1, padx=10, pady=10, sticky="nsew"
        )

        self.parent.radio_button_1 = customtkinter.CTkRadioButton(
            master=self.parent.radiobutton_frame,
            variable=self.parent.radio_tool_var,
            value=0,
            text="Circle Brush",
        )
        self.parent.radio_button_1.grid(
            row=1, column=0, pady=10, padx=20, sticky="nsew"
        )

        self.parent.radio_button_2 = customtkinter.CTkRadioButton(
            master=self.parent.radiobutton_frame,
            variable=self.parent.radio_tool_var,
            value=1,
            text="Rectangle Tool",
        )
        self.parent.radio_button_2.grid(
            row=2, column=0, pady=10, padx=20, sticky="nsew"
        )
        self.parent.radio_button_3 = customtkinter.CTkRadioButton(
            master=self.parent.radiobutton_frame,
            variable=self.parent.radio_tool_var,
            value=2,
            text="Fill Tool",
        )
        self.parent.radio_button_3.grid(
            row=3, column=0, pady=10, padx=20, sticky="nsew"
        )
        self.parent.radio_button_4 = customtkinter.CTkRadioButton(
            master=self.parent.radiobutton_frame,
            variable=self.parent.radio_tool_var,
            value=3,
            text="Text Tool",
        )
        self.parent.radio_button_4.grid(
            row=4, column=0, pady=10, padx=20, sticky="nsew"
        )
        self.parent.radio_button_5 = customtkinter.CTkRadioButton(
            master=self.parent.radiobutton_frame,
            variable=self.parent.radio_tool_var,
            value=4,
            text="Transform Tool",
        )
        self.parent.radio_button_5.grid(
            row=5, column=0, pady=10, padx=20, sticky="nsew"
        )
        self.parent.radio_button_6 = customtkinter.CTkRadioButton(
            master=self.parent.radiobutton_frame,
            variable=self.parent.radio_tool_var,
            value=5,
            text="Delete Tool",
        )
        self.parent.radio_button_6.grid(
            row=6, column=0, pady=10, padx=20, sticky="nsew"
        )
        self.parent.radio_button_7 = customtkinter.CTkRadioButton(
            master=self.parent.radiobutton_frame,
            variable=self.parent.radio_tool_var,
            value=6,
            text="Image Tool",
        )
        self.parent.radio_button_7.grid(
            row=7, column=0, pady=10, padx=20, sticky="nsew"
        )
        self.parent.radio_button_8 = customtkinter.CTkRadioButton(
            master=self.parent.radiobutton_frame,
            variable=self.parent.radio_tool_var,
            value=7,
            text="Calligraphy",
        )
        self.parent.radio_button_8.grid(
            row=8, column=0, pady=10, padx=20, sticky="nsew"
        )

        self.parent.appearance_mode_label = customtkinter.CTkLabel(
            self.parent.sidebar_frame, text="Appearance Mode:", anchor="w"
        )
        self.parent.appearance_mode_label.grid(row=6, column=0, padx=20, pady=(10, 0))
        self.parent.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(
            self.parent.sidebar_frame,
            values=["Light", "Dark", "System"],
            command=self.parent.change_appearance_mode_event,
        )
        self.parent.appearance_mode_optionemenu.grid(
            row=7, column=0, padx=20, pady=(10, 10)
        )
        self.parent.scaling_label = customtkinter.CTkLabel(
            self.parent.sidebar_frame, text="UI Scaling:", anchor="w"
        )
        self.parent.scaling_label.grid(
            row=8, column=0, padx=20, pady=(10, 0), sticky="sw"
        )
        self.parent.scaling_optionemenu = customtkinter.CTkOptionMenu(
            self.parent.sidebar_frame,
            values=["80%", "90%", "100%", "110%", "120%"],
            command=self.parent.change_scaling_event,
        )
        self.parent.scaling_optionemenu.grid(row=9, column=0, padx=20, pady=(10, 20))

        # Main Frame
        self.parent.main_frame = customtkinter.CTkFrame(
            self.parent,
            corner_radius=0,
        )
        self.parent.main_frame.grid(
            row=0, rowspan=4, column=1, padx=0, pady=0, sticky="NSEW"
        )
        self.parent.main_ribbon = tkinter.ttk.Notebook(self.parent.main_frame)

        # create tabview
        self.parent.tabview = customtkinter.CTkTabview(
            self.parent.main_frame,
            bg_color="transparent",
            fg_color="transparent",
        )
        self.parent.main_frame.grid_columnconfigure(0, weight=1)
        self.parent.main_frame.grid_rowconfigure(0, weight=1)
        self.parent.tabview.grid(
            row=0, column=0, padx=(20, 20), pady=(10, 10), sticky="NSEW"
        )
        self.parent.tabview.add("Canvas")
        self.parent.tabview.add("Genrated AI Image")
        self.parent.tabview.add("Webcam Image")

        # Canvas Tab
        # Main Frame grid configuration
        self.parent.main_frame.grid_columnconfigure(0, weight=1)
        self.parent.main_frame.grid_rowconfigure(0, weight=1)
