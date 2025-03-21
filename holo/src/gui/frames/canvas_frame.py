import customtkinter
from ...tools.tool_manager import ToolManager
from ...tools.drawing_tools import (
    CircleBrush,
    RectangleTool,
    FillTool,
    TransformTool,
    DeleteTool,
)


class CanvasFrame(customtkinter.CTkFrame):
    def __init__(self, master, tool_manager):
        super().__init__(master)
        self.tool_manager = tool_manager
        self._setup_canvas()
        self._initialize_drawing_tools()
        self._bind_events()

    def _setup_canvas(self):
        self.canvas = customtkinter.CTkCanvas(
            self, width=1280, height=720, bg="white", cursor="circle"
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def _initialize_drawing_tools(self):
        self.circle_brush = CircleBrush(self.canvas)
        self.rectangle_tool = RectangleTool(self.canvas)
        self.fill_tool = FillTool(self.canvas)
        self.transform_tool = TransformTool(self.canvas)
        self.delete_tool = DeleteTool(self.canvas)

    def _bind_events(self):
        """Bind canvas events"""
        self.canvas.bind("<Button-1>", self.canvas_mouse_down)
        self.canvas.bind("<ButtonRelease-1>", self.canvas_mouse_release)
        self.canvas.bind("<Motion>", self.mouse_move)
