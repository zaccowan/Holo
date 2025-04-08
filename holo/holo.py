# Imports for GUI library and styling system
import ctypes
from dotenv import load_dotenv
import customtkinter
from PIL import Image

# Imports for GUI modules
from GUI.BaseGUI import BaseGUI
from GUI.CanvasGUI import CanvasGUI
from GUI.GenAIGUI import GenAIGUI
from GUI.WebcamGUI import WebcamGUI

# Function Imports
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

from config import (
    DEFAULT_APPEARANCE_MODE,
    DEFAULT_COLOR_THEME,
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
    CanvasGUI,
    GenAIGUI,
    WebcamGUI,
):
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0

    def __init__(self):
        super().__init__()
        load_dotenv()

        # Helper functions and respective variables
        CanvasMouseFunctions.__init__(self)
        LayerPanelFunctions.__init__(self)
        WebcamFunctions.__init__(self)
        TextFunctions.__init__(self)
        ToolbarFunctions.__init__(self)
        HandTrackingCalibrationFunctions.__init__(self)
        WindowHelperFunctions.__init__(self)

        # GUI modules
        BaseGUI.__init__(self)
        CanvasGUI.__init__(self)
        GenAIGUI.__init__(self)
        WebcamGUI.__init__(self)

        # set default values
        self.appearance_mode_optionemenu.set("Dark")
        self.scaling_optionemenu.set("100%")
        self.apply_win_style("acrylic")


if __name__ == "__main__":
    app = Holo()
    app.mainloop()
