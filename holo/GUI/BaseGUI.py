import ctypes
import tkinter
import customtkinter
from PIL import Image
from pathlib import Path


# Import Function Modules

# System Imports
import sys

sys.path.append(str(Path(__file__).parent.parent))

from config import (
    DEFAULT_FRAME_WIDTH,
    DEFAULT_FRAME_HEIGHT,
)


class BaseGUI(customtkinter.CTk):

    def __init__(
        self,
        # parent,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        # self = parent
        self.title("Holo")
        self.geometry(f"{DEFAULT_FRAME_WIDTH}x{DEFAULT_FRAME_HEIGHT}")
        # set a minmum size for the window
        self.minsize(1280, 720)

        # Optional: Add F11 key binding to toggle fullscreen
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", lambda e: self.on_closing())

        # Override the protocol method to detect window close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.toplevel_window = None

        try:
            icon_path = (
                Path(__file__).parent.parent / "assets/images/holo_transparent.ico"
            )
            if not icon_path.exists():
                # Convert PNG to multi-size ICO
                png_path = (
                    Path(__file__).parent.parent / "assets/images/holo_transparent.png"
                )
                if png_path.exists():
                    with Image.open(png_path) as img:
                        # Convert to RGBA if needed
                        if img.mode != "RGBA":
                            img = img.convert("RGBA")

                        # Create multiple sizes for better quality
                        sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128)]
                        icons = []

                        for size in sizes:
                            resized_img = img.resize(size, Image.Resampling.LANCZOS)
                            icons.append(resized_img)

                        # Save as multi-size ICO
                        icons[0].save(
                            icon_path,
                            format="ICO",
                            sizes=sizes,
                            append_images=icons[1:],
                        )

            # Set window icon - use both methods for compatibility
            self.iconbitmap(default=str(icon_path))
            self.wm_iconbitmap(default=str(icon_path))

            # Set taskbar icon
            myappid = "Holo.Canvas.1.0"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

        except Exception as e:
            print(f"Error loading application icon: {e}")

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
        self.radio_button_8 = customtkinter.CTkRadioButton(
            master=self.radiobutton_frame,
            variable=self.radio_tool_var,
            value=7,
            text="Calligraphy",
        )
        self.radio_button_8.grid(row=8, column=0, pady=10, padx=20, sticky="nsew")

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
        self.tabview.add("Generated AI Image")
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
