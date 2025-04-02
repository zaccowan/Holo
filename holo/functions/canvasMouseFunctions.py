import tkinter
import customtkinter
from tkinter import filedialog
import math


################################
# Canvas Drawing Events
################################


def mouse_move(self_instance, event):
    self_instance.canvas.delete("temp_bbox")
    if self_instance.mouse_down:
        self_instance.mouse_active_coords["previous"] = (
            self_instance.mouse_active_coords["current"]
        )
        self_instance.mouse_active_coords["current"] = (event.x, event.y)

        if (
            self_instance.mouse_active_coords["previous"]
            != self_instance.mouse_active_coords["current"]
            and self_instance.mouse_active_coords["previous"] is not None
        ):
            match self_instance.active_tool:
                case "Circle Brush":
                    # Get stroke tag only once when starting a new stroke
                    if not hasattr(self_instance, "current_brush_tag"):
                        self_instance.current_brush_tag = self_instance.get_stroke_tag(
                            self_instance.active_tool
                        )
                        self_instance.add_layer_to_panel(
                            self_instance.current_brush_tag
                        )

                    self_instance.canvas.create_line(
                        self_instance.mouse_active_coords["previous"][0],
                        self_instance.mouse_active_coords["previous"][1],
                        self_instance.mouse_active_coords["current"][0],
                        self_instance.mouse_active_coords["current"][1],
                        fill=self_instance.hex_color,
                        width=self_instance.element_size,
                        capstyle=tkinter.ROUND,
                        smooth=True,
                        splinesteps=36,
                        tags=self_instance.current_brush_tag,
                    )
                case "Rectangle Tool":
                    self_instance.temp_rect = None
                    if self_instance.mouse_down:
                        self_instance.canvas.delete("temp_rect")
                        self_instance.temp_rect = self_instance.canvas.create_rectangle(
                            self_instance.mouse_down_canvas_coords[0],
                            self_instance.mouse_down_canvas_coords[1],
                            event.x,
                            event.y,
                            width=self_instance.element_size,
                            fill=str(self_instance.hex_color),
                            tags="temp_rect",
                        )
                case "Transform Tool":
                    if self_instance.transform_active:
                        match self_instance.transform_mode:
                            case "move":
                                dx = event.x - self_instance.mouse_down_canvas_coords[0]
                                dy = event.y - self_instance.mouse_down_canvas_coords[1]
                                for tag in self_instance.transform_tags:
                                    self_instance.canvas.move(tag, dx, dy)
                                self_instance.canvas.move("temp_bbox", dx, dy)

                            case "scale":
                                for tag in self_instance.transform_tags:
                                    bbox = self_instance.canvas.bbox(tag)
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
                                                self_instance.mouse_down_canvas_coords[
                                                    0
                                                ]
                                                - center_x
                                            )
                                            ** 2
                                            + (
                                                self_instance.mouse_down_canvas_coords[
                                                    1
                                                ]
                                                - center_y
                                            )
                                            ** 2
                                        )

                                        if start_dist > 0:
                                            scale = current_dist / start_dist
                                            scale = max(0.1, min(scale, 5.0))
                                            self_instance.canvas.scale(
                                                tag,
                                                center_x,
                                                center_y,
                                                scale,
                                                scale,
                                            )

                                            # Update bounding box
                                            self_instance.canvas.delete("temp_bbox")
                                            new_bbox = self_instance.canvas.bbox(tag)
                                            if new_bbox:
                                                self_instance.canvas.create_rectangle(
                                                    new_bbox[0] - 20,
                                                    new_bbox[1] - 20,
                                                    new_bbox[2] + 20,
                                                    new_bbox[3] + 20,
                                                    outline="#555555",
                                                    width=5,
                                                    tags="temp_bbox",
                                                )

                        self_instance.mouse_down_canvas_coords = (event.x, event.y)
                    else:
                        self_instance.update_temp_bbox(event)
                case "Calligraphy":
                    if self_instance.mouse_down:
                        # Get current hand depth if available
                        depth_ratio = 1.0
                        if (
                            hasattr(self_instance, "depth_tracking")
                            and self_instance.depth_tracking
                            and hasattr(self_instance, "depth_reference")
                        ):
                            depth_ratio = self_instance.get_current_depth_ratio()

                        # Adjust stroke width based on depth
                        stroke_width = self_instance.element_size * depth_ratio

                        # Get stroke tag only once when starting a new stroke
                        if not hasattr(self_instance, "current_calli_tag"):
                            self_instance.current_calli_tag = (
                                self_instance.get_stroke_tag(self_instance.active_tool)
                            )
                            self_instance.add_layer_to_panel(
                                self_instance.current_calli_tag
                            )

                        # Create calligraphy stroke
                        self_instance.canvas.create_line(
                            self_instance.mouse_active_coords["previous"][0],
                            self_instance.mouse_active_coords["previous"][1],
                            self_instance.mouse_active_coords["current"][0],
                            self_instance.mouse_active_coords["current"][1],
                            fill=self_instance.hex_color,
                            width=stroke_width,
                            capstyle=tkinter.ROUND,
                            smooth=True,
                            splinesteps=72,  # Double the spline steps for smoother curves
                            tags=self_instance.current_calli_tag,
                        )
    else:
        match self_instance.active_tool:
            case "Delete Tool":
                self_instance.update_temp_bbox(event)
            case "Transform Tool":
                self_instance.update_temp_bbox(event)
                item = self_instance.canvas.find_closest(event.x, event.y)[0]
                tag = self_instance.canvas.gettags(item)
                if not self_instance.transform_active:
                    self_instance.transform_active = True
                    self_instance.transform_tags = [tag[0]]
                    # Show bounding box for selected stroke
                    self_instance.canvas.delete("temp_bbox")
                    bbox = self_instance.canvas.bbox(tag[0])
                    if bbox:
                        self_instance.canvas.create_rectangle(
                            bbox[0] - 20,
                            bbox[1] - 20,
                            bbox[2] + 20,
                            bbox[3] + 20,
                            outline="#555555",
                            width=5,
                            tags="temp_bbox",
                        )
                elif tag[0] not in self_instance.transform_tags:
                    self_instance.transform_active = False
                    self_instance.transform_tags.clear()


def update_temp_bbox(self_instance, event):
    self_instance.canvas.delete("temp_bbox")
    item = self_instance.canvas.find_closest(event.x, event.y)
    if item:
        tag = self_instance.canvas.gettags(item[0])
        if tag:
            self_instance.active_bbox = self_instance.canvas.bbox(tag[0])
            if self_instance.active_tool == "Delete Tool":
                outline_color = "#FF5555"  # Slightly red color
            else:
                outline_color = "#555555"
            self_instance.canvas.create_rectangle(
                self_instance.active_bbox[0] - 20,
                self_instance.active_bbox[1] - 20,
                self_instance.active_bbox[2] + 20,
                self_instance.active_bbox[3] + 20,
                outline=outline_color,
                width=5,
                tags="temp_bbox",
            )


def canvas_mouse_down(self_instance, event):
    self_instance.mouse_down = True
    self_instance.mouse_down_canvas_coords = (event.x, event.y)
    # Initialize current position for brush strokes
    self_instance.mouse_active_coords["current"] = (event.x, event.y)
    match self_instance.active_tool:
        case "Transform Tool":
            item = self_instance.canvas.find_closest(event.x, event.y)[0]
            tag = self_instance.canvas.gettags(item)
            if not self_instance.transform_active:
                self_instance.transform_active = True
                self_instance.transform_tags = [tag[0]]
                # Show bounding box for selected stroke
                self_instance.canvas.delete("temp_bbox")
                bbox = self_instance.canvas.bbox(tag[0])
                if bbox:
                    self_instance.canvas.create_rectangle(
                        bbox[0] - 20,
                        bbox[1] - 20,
                        bbox[2] + 20,
                        bbox[3] + 20,
                        outline="#555555",
                        width=5,
                        tags="temp_bbox",
                    )
            elif tag[0] not in self_instance.transform_tags:
                self_instance.transform_active = False
                self_instance.transform_tags.clear()


def canvas_mouse_release(self_instance, event):
    self_instance.mouse_down = False
    self_instance.mouse_active_coords["previous"] = None
    self_instance.mouse_active_coords["current"] = None
    self_instance.mouse_release_canvas_coords = (event.x, event.y)

    # Clear brush tag when stroke is complete
    if hasattr(self_instance, "current_brush_tag"):
        delattr(self_instance, "current_brush_tag")

    # Clear stroke tags when stroke is complete
    if hasattr(self_instance, "current_calli_tag"):
        delattr(self_instance, "current_calli_tag")

    match self_instance.active_tool:
        case "Circle Brush":
            pass
        case "Rectangle Tool":
            self_instance.canvas.delete("temp_rect")
            stroke_tag = self_instance.get_stroke_tag(self_instance.active_tool)
            self_instance.canvas.create_rectangle(
                self_instance.mouse_down_canvas_coords[0],
                self_instance.mouse_down_canvas_coords[1],
                self_instance.mouse_release_canvas_coords[0],
                self_instance.mouse_release_canvas_coords[1],
                width=self_instance.element_size,
                fill=str(self_instance.hex_color),
                outline=str(self_instance.hex_color),
                tags=stroke_tag,
            )
            self_instance.add_layer_to_panel(stroke_tag)
        case "Text Tool":
            self_instance.open_text_entry_window()
        case "Delete Tool":
            self_instance.canvas.delete("temp_bbox")
            item = self_instance.canvas.find_closest(event.x, event.y)[0]
            tag = self_instance.canvas.gettags(item)
            if tag and "_" in tag[0]:  # Check for any valid element tag
                self_instance.delete_layer(tag[0])
        case "Image Tool":
            file_path = filedialog.askopenfilename(
                filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff")]
            )
            if file_path:
                self_instance.place_image(file_path, event.x, event.y)
        case "Fill Tool":
            stroke_tag = self_instance.get_stroke_tag(self_instance.active_tool)
            self_instance.canvas.create_rectangle(
                0,
                0,
                self_instance.canvas.winfo_width(),
                self_instance.canvas.winfo_height(),
                fill=self_instance.hex_color,
                tags=stroke_tag,
            )
            self_instance.add_layer_to_panel(stroke_tag)
