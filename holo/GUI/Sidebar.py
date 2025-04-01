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
