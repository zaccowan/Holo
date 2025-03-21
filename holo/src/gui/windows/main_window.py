import customtkinter
import tkinter
from tkinter import colorchooser, filedialog
from PIL import ImageGrab, Image, ImageTk
import ctypes
import threading
import cv2
import mediapipe as mp
import numpy as np

from ..frames.sidebar import Sidebar
from ..frames.canvas_frame import CanvasFrame
from ..frames.layer_panel import LayerPanel
from ...tools.tool_manager import ToolManager
from ...camera.camera_manager import CameraManager
from ...config.settings import GuiSettings, CameraSettings
from .text_entry import TextEntryWindow
from ...ai.image_generator import ImageGenerator


class MainWindow(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # Initialize managers
        self.tool_manager = ToolManager()
        self.camera_manager = CameraManager()
        self.image_generator = ImageGenerator()

        # Configure window
        self._setup_window()
        self._setup_ui()

        # Initialize state
        self.toplevel_window = None
        self.mouse_release_coords = (0, 0)
        self.file_path = None

        # Set window close handler
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _setup_window(self):
        customtkinter.set_appearance_mode(GuiSettings.APPEARANCE_MODE)
        customtkinter.set_default_color_theme(GuiSettings.DEFAULT_COLOR_THEME)

        self.title("Holo")
        self.geometry(f"{GuiSettings.WINDOW_WIDTH}x{GuiSettings.WINDOW_HEIGHT}")
        self.bind("<Escape>", lambda e: self.quit())

        # # Set window icon - using correct relative paths
        # logo_path = "../images/holo_transparent_scaled.png"
        # self.holo_logo = tkinter.PhotoImage(file=logo_path)
        # myappid = "Holo"
        # ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        # self.wm_iconbitmap(logo_path)
        # self.iconphoto(False, self.holo_logo)

        # Configure grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

    def _setup_ui(self):
        # Create main components
        self._setup_sidebar()
        self._setup_main_frame()
        self._setup_canvas()
        self._setup_layer_panel()

    def _setup_sidebar(self):
        """Setup the sidebar frame"""
        self.sidebar = Sidebar(self, self.tool_manager)
        self.sidebar.grid(row=0, column=0, rowspan=4, sticky="nsew")

    def _setup_main_frame(self):
        """Setup the main frame with tabview"""
        self.tabview = customtkinter.CTkTabview(
            self, bg_color="transparent", fg_color="transparent"
        )
        self.tabview.grid(row=0, column=1, padx=20, pady=10, sticky="nsew")

        # Add tabs
        self.tabview.add("Canvas")
        self.tabview.add("Generated AI Image")
        self.tabview.add("Webcam Image")

        # Configure tab layouts
        self.tabview.tab("Canvas").grid_columnconfigure((0, 1, 2), weight=1)
        self.tabview.tab("Canvas").grid_rowconfigure(0, weight=1)
        self.tabview.tab("Generated AI Image").grid_columnconfigure(0, weight=1)
        self.tabview.tab("Generated AI Image").grid_rowconfigure(0, weight=1)
        self.tabview.tab("Webcam Image").grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.tabview.tab("Webcam Image").grid_rowconfigure(4, weight=1)

        return self.tabview

    def _setup_canvas(self):
        """Setup the canvas with tools and controls"""
        # Canvas frame
        self.canvas_frame = CanvasFrame(self.tabview.tab("Canvas"), self.tool_manager)
        self.canvas_frame.grid(row=0, column=0, columnspan=3, sticky="nsew")

        # Generation and Saving Controls
        self._setup_canvas_controls()

    def _setup_canvas_controls(self):
        """Setup canvas controls for AI generation and saving"""
        self.prompt_entry = customtkinter.CTkEntry(
            self.tabview.tab("Canvas"),
            placeholder_text="Prompt to guide image generation...",
        )
        self.prompt_entry.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.generate_ai_image_btn = customtkinter.CTkButton(
            self.tabview.tab("Canvas"),
            fg_color="transparent",
            border_width=2,
            text="Generate AI Image",
            text_color=("gray10", "#DCE4EE"),
            command=self.generate_ai_image,
        )
        self.generate_ai_image_btn.grid(row=2, column=1, padx=20, pady=20, sticky="ew")

        self.save_canvas_btn = customtkinter.CTkButton(
            self.tabview.tab("Canvas"),
            fg_color="transparent",
            border_width=2,
            text="Save Drawing",
            text_color=("gray10", "#DCE4EE"),
            command=self.save_canvas,
        )
        self.save_canvas_btn.grid(row=2, column=2, padx=20, pady=20, sticky="ew")

    def _setup_layer_panel(self):
        """Setup the layer panel"""
        self.layer_panel = LayerPanel(
            self.tabview.tab("Canvas"), self.canvas_frame.canvas
        )
        self.layer_panel.grid(row=0, column=3, rowspan=3, sticky="ns", padx=5, pady=5)

    def open_text_entry_window(self):
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = TextEntryWindow(self)
        else:
            self.toplevel_window.focus()

    def generate_ai_image(self):
        """Generate AI image from canvas content"""
        self.save_canvas()
        input_image_path = self.file_path
        prompt = self.prompt_entry.get()

        def update_image_label(image):
            photo_image = ImageTk.PhotoImage(image=image)
            self.gen_ai_image_label.configure(text="")
            self.gen_ai_image_label.ai_photo_image = photo_image
            self.gen_ai_image_label.configure(image=photo_image)

        def run_generation():
            self.image_generator.preview_input(input_image_path)
            self.image_generator.generate_image(
                input_image_path, prompt, callback=update_image_label
            )

        generation_thread = threading.Thread(target=run_generation)
        generation_thread.start()

    def save_canvas(self):
        """Save canvas content to file"""
        self.file_path = filedialog.asksaveasfilename(
            defaultextension="*.png",
            filetypes=[("PNG Files", "*.png"), ("JPG Files", "*.jpg")],
        )
        if self.file_path:
            ImageGrab.grab(
                bbox=(
                    self.canvas_frame.canvas.winfo_rootx(),
                    self.canvas_frame.canvas.winfo_rooty(),
                    self.canvas_frame.canvas.winfo_rootx()
                    + self.canvas_frame.canvas.winfo_width()
                    - 4,
                    self.canvas_frame.canvas.winfo_rooty()
                    + self.canvas_frame.canvas.winfo_height()
                    - 4,
                )
            ).save(self.file_path)

    def set_canvas_text(self, text):
        """Set text on canvas at mouse release coordinates"""
        self.canvas_frame.canvas.create_text(
            self.mouse_release_coords[0],
            self.mouse_release_coords[1],
            text=text,
            font=customtkinter.CTkFont(size=self.tool_manager.element_size),
        )

    def on_closing(self):
        """Handle window closing"""
        if hasattr(self, "camera_manager"):
            self.camera_manager.close_camera()
        self.quit()
