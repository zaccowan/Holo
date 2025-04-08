import customtkinter


class TextFunctions:
    def __init__(self):
        self.canvas_text = None

    def open_text_entry_window(self):
        # Import here to avoid circular dependency
        from GUI.TextEntry import TextEntryWindow

        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = TextEntryWindow(self)
        else:
            self.toplevel_window.focus()

    def set_canvas_text(self, entry_text):
        self.canvas_text = entry_text
        stroke_tag = self.get_stroke_tag("Text Tool")
        self.canvas.create_text(
            self.mouse_release_canvas_coords[0],
            self.mouse_release_canvas_coords[1],
            text=entry_text,
            font=customtkinter.CTkFont(size=self.element_size),
            tags=stroke_tag,
        )
        self.add_layer_to_panel(stroke_tag)
