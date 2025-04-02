from tkinter import colorchooser
import customtkinter


################################
# Layer Window
################################
def add_layer_to_panel(self_instance, stroke_tag):
    layer_frame = customtkinter.CTkFrame(self_instance.layer_container)
    layer_frame.grid(
        row=len(self_instance.layer_buttons), column=0, pady=2, padx=5, sticky="nsw"
    )
    layer_frame.grid_columnconfigure(0, weight=1)

    # Create more descriptive label
    tool_type, number = stroke_tag.split("_")
    label_text = f"{tool_type.capitalize()} {number}"

    # Make the label clickable and highlight on hover
    layer_label = customtkinter.CTkLabel(
        layer_frame,
        text=label_text,
        cursor="hand2",
    )
    layer_label.grid(row=0, column=0, pady=2, padx=5, sticky="w")

    # Bind click event to select the stroke
    layer_label.bind(
        "<Button-1>", lambda e, tag=stroke_tag: self_instance.select_layer(tag)
    )

    # Dictionary to store buttons for managing references
    buttons = {}
    next_column = 1

    # Handle color edit button
    if tool_type in ["brush", "rect", "fill", "text"]:
        edit_button = customtkinter.CTkButton(
            layer_frame,
            text="",
            width=24,
            height=24,
            image=self_instance.edit_icon,
            command=lambda t=stroke_tag: self_instance.edit_layer_color(t),
        )
        edit_button.grid(row=0, column=next_column, pady=2, padx=2)
        buttons["edit_button"] = edit_button
        next_column += 1

    # Add text edit button only for text elements
    if tool_type == "text":
        edit_text_button = customtkinter.CTkButton(
            layer_frame,
            text="Edit Text",
            width=60,
            height=24,
            command=lambda t=stroke_tag: self_instance.edit_layer_text(t),
        )
        edit_text_button.grid(row=0, column=next_column, pady=2, padx=2)
        buttons["edit_text_button"] = edit_text_button
        next_column += 1

    # Delete button with icon
    delete_button = customtkinter.CTkButton(
        layer_frame,
        text="",
        width=24,
        height=24,
        image=self_instance.trash_icon,
        command=lambda t=stroke_tag: self_instance.delete_layer(t),
    )
    delete_button.grid(row=0, column=next_column, pady=2, padx=2)
    buttons["delete_button"] = delete_button

    # Store all components in the layer_buttons dictionary
    self_instance.layer_buttons[stroke_tag] = {
        "frame": layer_frame,
        "label": layer_label,
        **buttons,  # Unpack the buttons dictionary
    }


def delete_layer(self_instance, stroke_tag):
    """Delete a layer and update counters"""
    # Delete the stroke from canvas
    self_instance.canvas.delete(stroke_tag)

    # Update the counter for the tool type
    tool_type, number = stroke_tag.split("_")
    if tool_type in self_instance.tool_counters:
        self_instance.tool_counters[tool_type] = max(
            self_instance.tool_counters[tool_type], int(number)
        )

    # Delete the UI components
    if stroke_tag in self_instance.layer_buttons:
        layer_info = self_instance.layer_buttons[stroke_tag]
        layer_info["frame"].destroy()
        del self_instance.layer_buttons[stroke_tag]
        self_instance._reposition_layers()


def reposition_layers(self_instance):
    for idx, (tag, layer_info) in enumerate(self_instance.layer_buttons.items()):
        layer_info["frame"].grid(row=idx, column=0, pady=2, padx=5, sticky="ew")


def select_layer(self_instance, stroke_tag):
    # Check if layer is already selected
    if (
        hasattr(self_instance, "selected_layer")
        and self_instance.selected_layer == stroke_tag
    ):
        # Layer is already selected, show color picker
        color_code = colorchooser.askcolor(
            title="Choose stroke color",
            color=self_instance.canvas.itemcget(stroke_tag, "fill"),
        )
        if color_code:
            # Update the stroke color
            if "brush" in stroke_tag or "rect" in stroke_tag:
                self_instance.canvas.itemconfig(stroke_tag, fill=color_code[1])
                if "rect" in stroke_tag:
                    self_instance.canvas.itemconfig(stroke_tag, outline=color_code[1])
            elif "text" in stroke_tag:
                self_instance.canvas.itemconfig(stroke_tag, fill=color_code[1])
            elif "fill" in stroke_tag:
                self_instance.canvas.itemconfig(stroke_tag, fill=color_code[1])
    else:
        # Reset previous selections
        for layer_info in self_instance.layer_buttons.values():
            layer_info["frame"].configure(fg_color=("gray86", "gray17"))
            layer_info["label"].configure(fg_color=("gray86", "gray17"))

        # Highlight selected layer
        self_instance.layer_buttons[stroke_tag]["frame"].configure(
            fg_color=("#4477AA", "#4477AA")
        )
        self_instance.layer_buttons[stroke_tag]["label"].configure(
            fg_color=("#4477AA", "#4477AA")
        )

        # Set transform tool as active
        self_instance.radio_tool_var.set(4)  # Index for Transform Tool
        self_instance.transform_active = True
        self_instance.transform_tags = [stroke_tag]
        self_instance.selected_layer = stroke_tag

        # Show bounding box for selected stroke
        self_instance.canvas.delete("temp_bbox")
        bbox = self_instance.canvas.bbox(stroke_tag)
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


def edit_layer_color(self_instance, stroke_tag):
    """Edit the color of a layer"""
    color_code = colorchooser.askcolor(
        title="Choose stroke color",
        color=self_instance.canvas.itemcget(stroke_tag, "fill"),
    )
    if color_code:
        # Update the stroke color based on type
        if "brush" in stroke_tag or "rect" in stroke_tag:
            self_instance.canvas.itemconfig(stroke_tag, fill=color_code[1])
            if "rect" in stroke_tag:
                self_instance.canvas.itemconfig(stroke_tag, outline=color_code[1])
        elif "text" in stroke_tag:
            self_instance.canvas.itemconfig(stroke_tag, fill=color_code[1])
        elif "fill" in stroke_tag:
            self_instance.canvas.itemconfig(stroke_tag, fill=color_code[1])


def edit_layer_text(self_instance, stroke_tag):
    """Change the font size of a text element"""
    try:
        # Get current text
        current_text = self_instance.canvas.itemcget(stroke_tag, "text")

        # Create new font with current element_size
        new_font = customtkinter.CTkFont(size=self_instance.element_size)

        # Update the text element's font
        self_instance.canvas.itemconfig(stroke_tag, font=new_font)

        # Update bounding box if transform tool is active
        if (
            self_instance.transform_active
            and stroke_tag in self_instance.transform_tags
        ):
            self_instance.canvas.delete("temp_bbox")
            bbox = self_instance.canvas.bbox(stroke_tag)
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

    except Exception as e:
        print(f"Error updating text size: {e}")
