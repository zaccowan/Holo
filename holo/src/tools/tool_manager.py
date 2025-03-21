from ..config.settings import ToolSettings, GuiSettings


class ToolManager:
    def __init__(self):
        self.tools = ToolSettings.TOOLS
        self.tool_cursors = ToolSettings.TOOL_CURSORS
        self.active_tool = "Circle Brush"
        self.hex_color = GuiSettings.DEFAULT_HEX_COLOR
        self.element_size = GuiSettings.DEFAULT_ELEMENT_SIZE
        self.stroke_counter = 0
        self.transform_active = False
        self.transform_tags = []
        self.active_bbox = None

    def set_active_tool(self, tool_index):
        """Set the active tool and return the appropriate cursor"""
        self.active_tool = self.tools.get(tool_index)
        return self.tool_cursors.get(self.active_tool)

    def set_color(self, hex_color):
        """Set the current color"""
        self.hex_color = hex_color

    def set_element_size(self, size):
        """Set the current element size"""
        self.element_size = int(size)

    def increment_stroke_counter(self):
        """Increment and return the stroke counter"""
        self.stroke_counter += 1
        return self.stroke_counter

    def get_stroke_tag(self):
        """Get the current stroke tag"""
        return f"brush_stroke{self.stroke_counter}"

    def toggle_transform(self, active=None):
        """Toggle or set the transform state"""
        if active is None:
            self.transform_active = not self.transform_active
        else:
            self.transform_active = active

    def clear_transform_tags(self):
        """Clear transform tags"""
        self.transform_tags = []

    def add_transform_tag(self, tag):
        """Add a tag to transform"""
        self.transform_tags.append(tag)
