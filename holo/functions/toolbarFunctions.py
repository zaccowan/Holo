import math
from tkinter import colorchooser
import customtkinter
from PIL import Image, ImageTk

from config import (
    TOOL_DICT,
)

################################
# Toolbar Functions
################################


class ToolbarFunctions:
    def __init__(self):
        self.hex_color = "#000000"
        self.element_size = 5
        self.tool_dict = TOOL_DICT
        self.active_tool = "Circle Brush"

    def choose_color(self, event):
        self.color_code = colorchooser.askcolor(title="Choose color")
        if self.color_code:
            self.hex_color = self.color_code[1]
            self.color_label.configure(
                text=f"Element Color: {self.hex_color}",
                fg_color=self.hex_color,
            )

    def set_element_size(self, event):
        self.element_size = int(self.element_size_slider.get())
        self.element_size_label.configure(text=f"Element Size: {self.element_size}")

    def set_active_tool(self, *args):
        self.active_tool = self.tool_dict.get(self.radio_tool_var.get())
        match self.active_tool:
            case "Circle Brush":
                self.canvas.configure(cursor="circle")
                self.transform_controls.grid_remove()  # Hide controls
                self.transform_active = False
                self.transform_tags.clear()

            case "Rectangle Tool":
                self.canvas.configure(cursor="tcross")
                self.transform_controls.grid_remove()  # Hide controls
                self.transform_active = False
                self.transform_tags.clear()

            case "Fill Tool":
                self.canvas.configure(cursor="spraycan")
                self.transform_controls.grid_remove()  # Hide controls
                self.transform_active = False
                self.transform_tags.clear()

            case "Text Tool":
                self.canvas.configure(cursor="xterm")
                self.transform_controls.grid_remove()  # Hide controls
                self.transform_active = False
                self.transform_tags.clear()

            case "Transform Tool":
                self.canvas.configure(cursor="fleur")
                # Show transform controls
                self.transform_controls.grid(
                    row=0, column=0, columnspan=3, sticky="ew", pady=(0, 5)
                )
                # Initialize transform state
                self.transform_mode = "move"
                self.move_btn.configure(fg_color="#4477AA")
                self.scale_btn.configure(fg_color="transparent")

            case "Delete Tool":
                self.canvas.configure(cursor="X_cursor")
                self.transform_controls.grid_remove()  # Hide controls
                self.transform_active = False
                self.transform_tags.clear()

            case "Image Tool":
                self.canvas.configure(cursor="plus")
                self.transform_controls.grid_remove()  # Hide controls
                self.transform_active = False
                self.transform_tags.clear()

    def place_image(self, file_path, x, y):
        """Place an image on the canvas centered at the click position"""
        # Load and convert the image
        image = Image.open(file_path)

        # Calculate scaling to fit canvas while maintaining aspect ratio
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        img_width, img_height = image.size

        # Calculate scale factor
        width_ratio = canvas_width / img_width
        height_ratio = canvas_height / img_height
        scale_factor = min(width_ratio, height_ratio) * 0.8  # 80% of max size

        # Scale image
        new_width = int(img_width * scale_factor)
        new_height = int(img_height * scale_factor)
        resized_image = image.resize((new_width, new_height), Image.LANCZOS)

        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(resized_image)

        # Store the original image for future scaling operations
        photo._photo_original = image

        # Calculate centered position
        x_centered = x - (new_width // 2)
        y_centered = y - (new_height // 2)

        # Create image on canvas
        stroke_tag = self.get_stroke_tag(self.active_tool)

        image_id = self.canvas.create_image(
            x_centered,
            y_centered,
            image=photo,
            anchor="nw",
            tags=stroke_tag,
        )

        # Initialize photo_references dictionary if it doesn't exist
        if not hasattr(self.canvas, "photo_references"):
            self.canvas.photo_references = {}

        # Store reference to prevent garbage collection using the stroke_tag as key
        self.canvas.photo_references[stroke_tag] = photo

        # Add to layer panel
        self.add_layer_to_panel(stroke_tag)

    def get_stroke_tag(self, tool_name):
        tool_prefix = {
            "Circle Brush": "brush",
            "Rectangle Tool": "rect",
            "Fill Tool": "fill",
            "Text Tool": "text",
            "Image Tool": "image",
            "Calligraphy": "calli",  # Add calligraphy prefix
        }
        prefix = tool_prefix.get(tool_name, "element")
        if prefix not in self.tool_counters:
            self.tool_counters[prefix] = 0  # Initialize counter if needed
        self.tool_counters[prefix] += 1
        return f"{prefix}_{self.tool_counters[prefix]}"

    def set_transform_mode(self, mode):
        """Set the current transform mode and update button appearances"""
        self.transform_mode = mode

        # Update button colors (remove rotate from buttons dictionary)
        buttons = {"move": self.move_btn, "scale": self.scale_btn}

        for btn_mode, btn in buttons.items():
            if btn_mode == mode:
                btn.configure(fg_color="#4477AA")
            else:
                btn.configure(fg_color="transparent")

    def transform_element(self, event):
        """Handle element transformation based on current mode"""
        if not self.transform_active or not self.transform_tags:
            return

        match self.transform_mode:
            case "move":
                # Existing move logic
                dx = event.x - self.mouse_down_canvas_coords[0]
                dy = event.y - self.mouse_down_canvas_coords[1]
                for tag in self.transform_tags:
                    self.canvas.move(tag, dx, dy)
                self.canvas.move("temp_bbox", dx, dy)

            case "scale":
                # Scale from center
                for tag in self.transform_tags:
                    bbox = self.canvas.bbox(tag)
                    if bbox:
                        center_x = (bbox[0] + bbox[2]) / 2
                        center_y = (bbox[1] + bbox[3]) / 2

                        # Prevent division by zero and invalid scaling
                        try:
                            dx = event.x - center_x
                            dy = event.y - center_y
                            old_dx = self.mouse_down_canvas_coords[0] - center_x
                            old_dy = self.mouse_down_canvas_coords[1] - center_y

                            # Calculate distance ratios for scaling
                            new_dist = math.sqrt(dx * dx + dy * dy)
                            old_dist = math.sqrt(old_dx * old_dx + old_dy * old_dy)

                            if old_dist > 0:  # Prevent division by zero
                                scale = new_dist / old_dist
                                # Limit scale factor to reasonable range
                                scale = max(0.1, min(scale, 10.0))

                                # Check if this is an image tag
                                if (
                                    tag.startswith("image_")
                                    and hasattr(self.canvas, "photo_references")
                                    and tag in self.canvas.photo_references
                                ):
                                    # Get the item ID for this tag
                                    items = self.canvas.find_withtag(tag)
                                    if items:
                                        # Get current position
                                        current_coords = self.canvas.coords(items[0])

                                        # Get the original image reference
                                        photo_ref = self.canvas.photo_references[tag]
                                        if hasattr(photo_ref, "_photo_original"):
                                            # Get original PIL image if stored
                                            original_img = photo_ref._photo_original
                                        else:
                                            # If not available, we can't scale it properly
                                            self.canvas.scale(
                                                tag, center_x, center_y, scale, scale
                                            )
                                            continue

                                        # Calculate new size
                                        current_width = bbox[2] - bbox[0]
                                        current_height = bbox[3] - bbox[1]
                                        new_width = int(current_width * scale)
                                        new_height = int(current_height * scale)

                                        # Resize the image
                                        resized_img = original_img.resize(
                                            (new_width, new_height), Image.LANCZOS
                                        )
                                        new_photo = ImageTk.PhotoImage(resized_img)

                                        # Store reference to prevent garbage collection
                                        self.canvas.photo_references[tag] = new_photo
                                        # Store original for future scaling
                                        new_photo._photo_original = original_img

                                        # Update image on canvas (delete and recreate)
                                        self.canvas.delete(items[0])
                                        new_x = center_x - (new_width / 2)
                                        new_y = center_y - (new_height / 2)
                                        self.canvas.create_image(
                                            new_x,
                                            new_y,
                                            image=new_photo,
                                            anchor="nw",
                                            tags=tag,
                                        )
                                else:
                                    # For non-image elements, use regular scaling
                                    self.canvas.scale(
                                        tag, center_x, center_y, scale, scale
                                    )
                        except (ZeroDivisionError, ValueError):
                            pass  # Skip scaling if calculations are invalid

        # Update mouse position for next frame
        self.mouse_down_canvas_coords = (event.x, event.y)
