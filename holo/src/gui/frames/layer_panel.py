import customtkinter


class LayerPanel(customtkinter.CTkFrame):
    def __init__(self, master, canvas):
        super().__init__(master, width=200, corner_radius=0)
        self.canvas = canvas
        self.layer_buttons = {}
        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # Panel label
        self.layer_panel_label = customtkinter.CTkLabel(
            self, text="Layers", font=customtkinter.CTkFont(size=16, weight="bold")
        )
        self.layer_panel_label.grid(row=0, column=0, pady=5, padx=5)

        # Scrollable layer container
        self.layer_container = customtkinter.CTkScrollableFrame(
            self, width=180, height=600
        )
        self.layer_container.grid(row=1, column=0, pady=5, padx=5, sticky="nsew")
