import tkinter
import customtkinter
from PIL import ImageGrab, Image, ImageTk


class DrawingTool:
    def __init__(self, canvas):
        if canvas is None:
            raise ValueError("Canvas cannot be None")
        self.canvas = canvas
        self.stroke_counter = 0
        self.mouse_down = False
        self.mouse_active_coords = {"previous": None, "current": None}
        self.mouse_down_canvas_coords = (0, 0)
        self.mouse_release_canvas_coords = (0, 0)


class CircleBrush(DrawingTool):
    def draw(self, event, hex_color, element_size):
        if self.mouse_active_coords["previous"] != self.mouse_active_coords["current"]:
            self.canvas.create_line(
                self.mouse_active_coords["previous"][0],
                self.mouse_active_coords["previous"][1],
                self.mouse_active_coords["current"][0],
                self.mouse_active_coords["current"][1],
                fill=hex_color,
                width=element_size,
                capstyle=tkinter.ROUND,
                smooth=True,
                splinesteps=36,
                tags=f"brush_stroke{self.stroke_counter}",
            )


class RectangleTool(DrawingTool):
    def __init__(self, canvas):
        super().__init__(canvas)
        self.temp_rect = None

    def draw_temp(self, event, hex_color, element_size):
        self.canvas.delete("temp_rect")
        self.temp_rect = self.canvas.create_rectangle(
            self.mouse_down_canvas_coords[0],
            self.mouse_down_canvas_coords[1],
            event.x,
            event.y,
            width=element_size,
            fill=hex_color,
            tags="temp_rect",
        )

    def draw_final(self, event, hex_color, element_size):
        self.canvas.delete("temp_rect")
        self.canvas.create_rectangle(
            self.mouse_down_canvas_coords[0],
            self.mouse_down_canvas_coords[1],
            self.mouse_release_canvas_coords[0],
            self.mouse_release_canvas_coords[1],
            width=element_size,
            fill=hex_color,
            outline=hex_color,
            tags=f"brush_stroke{self.stroke_counter}",
        )


class FillTool(DrawingTool):
    def fill(self, hex_color):
        self.canvas.create_rectangle(
            0,
            0,
            self.canvas.winfo_width(),
            self.canvas.winfo_height(),
            fill=hex_color,
            tags=f"brush_stroke{self.stroke_counter}",
        )


class TransformTool(DrawingTool):
    def __init__(self, canvas):
        super().__init__(canvas)
        self.transform_active = False
        self.transform_tags = []
        self.active_bbox = None

    def start_transform(self, event):
        item = self.canvas.find_closest(event.x, event.y)[0]
        tag = self.canvas.gettags(item)
        if not self.transform_active:
            self.transform_active = True
            self.transform_tags = [tag[0]]
            self.show_bounding_box(tag[0])
        elif tag[0] not in self.transform_tags:
            self.transform_active = False
            self.transform_tags.clear()

    def show_bounding_box(self, tag):
        self.canvas.delete("temp_bbox")
        bbox = self.canvas.bbox(tag)
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

    def transform(self, event):
        if self.transform_active:
            dx = event.x - self.mouse_down_canvas_coords[0]
            dy = event.y - self.mouse_down_canvas_coords[1]
            for tag in self.transform_tags:
                self.canvas.move(tag, dx, dy)
            self.canvas.move("temp_bbox", dx, dy)
            self.mouse_down_canvas_coords = (event.x, event.y)


class DeleteTool(DrawingTool):
    def show_delete_box(self, event):
        self.canvas.delete("temp_bbox")
        item = self.canvas.find_closest(event.x, event.y)[0]
        tag = self.canvas.gettags(item)
        if tag:
            self.active_bbox = self.canvas.bbox(tag[0])
            self.canvas.create_rectangle(
                self.active_bbox[0] - 20,
                self.active_bbox[1] - 20,
                self.active_bbox[2] + 20,
                self.active_bbox[3] + 20,
                outline="#FF5555",
                width=5,
                tags="temp_bbox",
            )
