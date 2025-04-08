import tkinter
import customtkinter
from tkinter import filedialog
import math


################################
# Canvas Drawing Events
################################


class CanvasMouseFunctions:
    def __init__(self):
        # Initialize necessary attributes that subclasses will need
        self.mouse_down = False
        self.mouse_active_coords = {
            "previous": None,
            "current": None,
        }
        self.mouse_down_canvas_coords = (0, 0)
        self.mouse_release_canvas_coords = (0, 0)
        self.transform_active = False
        self.transform_tags = []
        self.active_bbox = None

    def mouse_move(self, event):
        self.canvas.delete("temp_bbox")
        if self.mouse_down:
            self.mouse_active_coords["previous"] = self.mouse_active_coords["current"]
            self.mouse_active_coords["current"] = (event.x, event.y)

            if (
                self.mouse_active_coords["previous"]
                != self.mouse_active_coords["current"]
                and self.mouse_active_coords["previous"] is not None
            ):
                match self.active_tool:
                    case "Circle Brush":
                        # Get stroke tag only once when starting a new stroke
                        if not hasattr(self, "current_brush_tag"):
                            self.current_brush_tag = self.get_stroke_tag(
                                self.active_tool
                            )
                            self.add_layer_to_panel(self.current_brush_tag)

                        self.canvas.create_line(
                            self.mouse_active_coords["previous"][0],
                            self.mouse_active_coords["previous"][1],
                            self.mouse_active_coords["current"][0],
                            self.mouse_active_coords["current"][1],
                            fill=self.hex_color,
                            width=self.element_size,
                            capstyle=tkinter.ROUND,
                            smooth=True,
                            splinesteps=36,
                            tags=self.current_brush_tag,
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
                        if self.transform_active:
                            match self.transform_mode:
                                case "move":
                                    dx = event.x - self.mouse_down_canvas_coords[0]
                                    dy = event.y - self.mouse_down_canvas_coords[1]
                                    for tag in self.transform_tags:
                                        self.canvas.move(tag, dx, dy)
                                    self.canvas.move("temp_bbox", dx, dy)

                                case "scale":
                                    for tag in self.transform_tags:
                                        bbox = self.canvas.bbox(tag)
                                        if bbox:
                                            center_x = (bbox[0] + bbox[2]) / 2
                                            center_y = (bbox[1] + bbox[3]) / 2

                                            # Calculate distance from center
                                            current_dist = math.sqrt(
                                                (event.x - center_x) ** 2
                                                + (event.y - center_y) ** 2
                                            )
                                            start_dist = math.sqrt(
                                                (
                                                    self.mouse_down_canvas_coords[0]
                                                    - center_x
                                                )
                                                ** 2
                                                + (
                                                    self.mouse_down_canvas_coords[1]
                                                    - center_y
                                                )
                                                ** 2
                                            )

                                            if start_dist > 0:
                                                scale = current_dist / start_dist
                                                scale = max(0.1, min(scale, 5.0))
                                                self.canvas.scale(
                                                    tag,
                                                    center_x,
                                                    center_y,
                                                    scale,
                                                    scale,
                                                )

                                                # Update bounding box
                                                self.canvas.delete("temp_bbox")
                                                new_bbox = self.canvas.bbox(tag)
                                                if new_bbox:
                                                    self.canvas.create_rectangle(
                                                        new_bbox[0] - 20,
                                                        new_bbox[1] - 20,
                                                        new_bbox[2] + 20,
                                                        new_bbox[3] + 20,
                                                        outline="#555555",
                                                        width=5,
                                                        tags="temp_bbox",
                                                    )

                            self.mouse_down_canvas_coords = (event.x, event.y)
                        else:
                            self.update_temp_bbox(event)
                    case "Calligraphy":
                        if self.mouse_down:
                            # Get current hand depth if available
                            depth_ratio = 1.0
                            if (
                                hasattr(self, "depth_tracking")
                                and self.depth_tracking
                                and hasattr(self, "depth_reference")
                            ):
                                depth_ratio = self.get_current_depth_ratio()

                            # Adjust stroke width based on depth
                            stroke_width = self.element_size * depth_ratio

                            # Get stroke tag only once when starting a new stroke
                            if not hasattr(self, "current_calli_tag"):
                                self.current_calli_tag = self.get_stroke_tag(
                                    self.active_tool
                                )
                                self.add_layer_to_panel(self.current_calli_tag)

                            # Create calligraphy stroke
                            self.canvas.create_line(
                                self.mouse_active_coords["previous"][0],
                                self.mouse_active_coords["previous"][1],
                                self.mouse_active_coords["current"][0],
                                self.mouse_active_coords["current"][1],
                                fill=self.hex_color,
                                width=stroke_width,
                                capstyle=tkinter.ROUND,
                                smooth=True,
                                splinesteps=72,  # Double the spline steps for smoother curves
                                tags=self.current_calli_tag,
                            )
        else:
            match self.active_tool:
                case "Delete Tool":
                    self.update_temp_bbox(event)
                case "Transform Tool":
                    self.update_temp_bbox(event)
                    item = self.canvas.find_closest(event.x, event.y)[0]
                    tag = self.canvas.gettags(item)
                    if not self.transform_active:
                        self.transform_active = True
                        self.transform_tags = [tag[0]]
                        # Show bounding box for selected stroke
                        self.canvas.delete("temp_bbox")
                        bbox = self.canvas.bbox(tag[0])
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
                    elif tag[0] not in self.transform_tags:
                        self.transform_active = False
                        self.transform_tags.clear()

    def update_temp_bbox(self, event):
        self.canvas.delete("temp_bbox")
        item = self.canvas.find_closest(event.x, event.y)
        if item:
            tag = self.canvas.gettags(item[0])
            if tag:
                self.active_bbox = self.canvas.bbox(tag[0])
                if self.active_tool == "Delete Tool":
                    outline_color = "#FF5555"  # Slightly red color
                else:
                    outline_color = "#555555"
                self.canvas.create_rectangle(
                    self.active_bbox[0] - 20,
                    self.active_bbox[1] - 20,
                    self.active_bbox[2] + 20,
                    self.active_bbox[3] + 20,
                    outline=outline_color,
                    width=5,
                    tags="temp_bbox",
                )

    def canvas_mouse_down(self, event):
        self.mouse_down = True
        self.mouse_down_canvas_coords = (event.x, event.y)
        # Initialize current position for brush strokes
        self.mouse_active_coords["current"] = (event.x, event.y)
        match self.active_tool:
            case "Transform Tool":
                item = self.canvas.find_closest(event.x, event.y)[0]
                tag = self.canvas.gettags(item)
                if not self.transform_active:
                    self.transform_active = True
                    self.transform_tags = [tag[0]]
                    # Show bounding box for selected stroke
                    self.canvas.delete("temp_bbox")
                    bbox = self.canvas.bbox(tag[0])
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
                elif tag[0] not in self.transform_tags:
                    self.transform_active = False
                    self.transform_tags.clear()

    def canvas_mouse_release(self, event):
        self.mouse_down = False
        self.mouse_active_coords["previous"] = None
        self.mouse_active_coords["current"] = None
        self.mouse_release_canvas_coords = (event.x, event.y)

        # Clear brush tag when stroke is complete
        if hasattr(self, "current_brush_tag"):
            delattr(self, "current_brush_tag")

        # Clear stroke tags when stroke is complete
        if hasattr(self, "current_calli_tag"):
            delattr(self, "current_calli_tag")

        match self.active_tool:
            case "Circle Brush":
                pass
            case "Rectangle Tool":
                self.canvas.delete("temp_rect")
                stroke_tag = self.get_stroke_tag(self.active_tool)
                self.canvas.create_rectangle(
                    self.mouse_down_canvas_coords[0],
                    self.mouse_down_canvas_coords[1],
                    self.mouse_release_canvas_coords[0],
                    self.mouse_release_canvas_coords[1],
                    width=self.element_size,
                    fill=str(self.hex_color),
                    outline=str(self.hex_color),
                    tags=stroke_tag,
                )
                self.add_layer_to_panel(stroke_tag)
            case "Text Tool":
                self.open_text_entry_window()
            case "Delete Tool":
                self.canvas.delete("temp_bbox")
                item = self.canvas.find_closest(event.x, event.y)[0]
                tag = self.canvas.gettags(item)
                if tag and "_" in tag[0]:  # Check for any valid element tag
                    self.delete_layer(tag[0])
            case "Image Tool":
                file_path = filedialog.askopenfilename(
                    filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff")]
                )
                if file_path:
                    self.place_image(file_path, event.x, event.y)
            case "Fill Tool":
                stroke_tag = self.get_stroke_tag(self.active_tool)
                self.canvas.create_rectangle(
                    0,
                    0,
                    self.canvas.winfo_width(),
                    self.canvas.winfo_height(),
                    fill=self.hex_color,
                    tags=stroke_tag,
                )
                self.add_layer_to_panel(stroke_tag)
