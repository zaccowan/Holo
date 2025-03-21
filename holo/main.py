from src.gui.windows.main_window import MainWindow
from src.gui.frames.sidebar import Sidebar
from src.gui.frames.canvas_frame import CanvasFrame
from src.gui.frames.camera_frame import CameraFrame
from src.gui.frames.layer_panel import LayerPanel
from src.tools.tool_manager import ToolManager
from src.tools.drawing_tools import (
    CircleBrush,
    RectangleTool,
    FillTool,
    TransformTool,
    DeleteTool,
)
from src.camera.camera_manager import CameraManager
from src.camera.hand_tracker import HandTracker
from src.ai.image_generator import ImageGenerator
from src.config.settings import (
    GuiSettings,
    CameraSettings,
    HandTrackingSettings,
    ToolSettings,
    AISettings,
)


class HoloApp(MainWindow):
    def __init__(self):
        super().__init__()

        # Initialize managers
        self.tool_manager = ToolManager()
        self.camera_manager = CameraManager()
        self.image_generator = ImageGenerator()

        # Setup main UI components
        self._setup_window()
        self._setup_ui()

    def _setup_window(self):
        """Initialize main window settings"""
        super()._setup_window()
        self.bind("<Escape>", lambda e: self.quit())
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _setup_ui(self):
        """Setup all UI components"""
        # Create sidebar
        self.sidebar = Sidebar(self, self.tool_manager)
        self.sidebar.grid(row=0, column=0, rowspan=4, sticky="nsew")

        # Create main frame with tabs
        self.main_frame = self._setup_main_frame()
        self.main_frame.grid(row=0, column=1, sticky="nsew")

        # Setup canvas tab
        self.canvas_frame = CanvasFrame(self.tabview.tab("Canvas"), self.tool_manager)
        self.canvas_frame.grid(row=0, column=0, sticky="nsew")

        # Setup layer panel
        self.layer_panel = LayerPanel(
            self.tabview.tab("Canvas"), self.canvas_frame.canvas
        )
        self.layer_panel.grid(row=0, column=1, sticky="ns")

        # Setup camera frame
        self.camera_frame = CameraFrame(self.tabview.tab("Webcam Image"))
        self.camera_frame.grid(row=0, column=0, sticky="nsew")

        # Configure grid weights
        self.grid_columnconfigure(1, weight=1)
        self.tabview.tab("Canvas").grid_columnconfigure(0, weight=1)

    def on_closing(self):
        """Handle application closing"""
        if hasattr(self, "camera_manager"):
            self.camera_manager.close_camera()
        self.quit()


if __name__ == "__main__":
    app = HoloApp()
    app.mainloop()
