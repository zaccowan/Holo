from tkinter import colorchooser
import customtkinter


################################
# Toolbar Functions
################################


def choose_color(self_instance, event):
    self_instance.color_code = colorchooser.askcolor(title="Choose color")
    if self_instance.color_code:
        self_instance.hex_color = self_instance.color_code[1]
        self_instance.color_label.configure(
            text=f"Element Color: {self_instance.hex_color}",
            fg_color=self_instance.hex_color,
        )


def set_element_size(self_instance, event):
    self_instance.element_size = int(self_instance.element_size_slider.get())
    self_instance.element_size_label.configure(
        text=f"Element Size: {self_instance.element_size}"
    )


def set_active_tool(self_instance, *args):
    self_instance.active_tool = self_instance.tool_dict.get(
        self_instance.radio_tool_var.get()
    )
    match self_instance.active_tool:
        case "Circle Brush":
            self_instance.canvas.configure(cursor="circle")
            self_instance.transform_controls.grid_remove()  # Hide controls
            self_instance.transform_active = False
            self_instance.transform_tags.clear()

        case "Rectangle Tool":
            self_instance.canvas.configure(cursor="tcross")
            self_instance.transform_controls.grid_remove()  # Hide controls
            self_instance.transform_active = False
            self_instance.transform_tags.clear()

        case "Fill Tool":
            self_instance.canvas.configure(cursor="spraycan")
            self_instance.transform_controls.grid_remove()  # Hide controls
            self_instance.transform_active = False
            self_instance.transform_tags.clear()

        case "Text Tool":
            self_instance.canvas.configure(cursor="xterm")
            self_instance.transform_controls.grid_remove()  # Hide controls
            self_instance.transform_active = False
            self_instance.transform_tags.clear()

        case "Transform Tool":
            self_instance.canvas.configure(cursor="fleur")
            # Show transform controls
            self_instance.transform_controls.grid(
                row=0, column=0, columnspan=3, sticky="ew", pady=(0, 5)
            )
            # Initialize transform state
            self_instance.transform_mode = "move"
            self_instance.move_btn.configure(fg_color="#4477AA")
            self_instance.scale_btn.configure(fg_color="transparent")

        case "Delete Tool":
            self_instance.canvas.configure(cursor="X_cursor")
            self_instance.transform_controls.grid_remove()  # Hide controls
            self_instance.transform_active = False
            self_instance.transform_tags.clear()

        case "Image Tool":
            self_instance.canvas.configure(cursor="plus")
            self_instance.transform_controls.grid_remove()  # Hide controls
            self_instance.transform_active = False
            self_instance.transform_tags.clear()


def open_text_entry_window(
    self_instance,
):
    if (
        self_instance.toplevel_window is None
        or not self_instance.toplevel_window.winfo_exists()
    ):
        self_instance.toplevel_window = TextEntryWindow(
            self_instance
        )  # create window if its None or destroyed
    else:
        self_instance.toplevel_window.focus()  # if window exists focus it


def set_canvas_text(self_instance, entry_text):
    self_instance.canvas_text = entry_text
    stroke_tag = self_instance.get_stroke_tag("Text Tool")
    self_instance.canvas.create_text(
        self_instance.mouse_release_canvas_coords[0],
        self_instance.mouse_release_canvas_coords[1],
        text=entry_text,
        font=customtkinter.CTkFont(size=self_instance.element_size),
        tags=stroke_tag,
    )
    self_instance.add_layer_to_panel(stroke_tag)
