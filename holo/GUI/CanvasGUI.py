import tkinter
import customtkinter


class CanvasGUI:
    def __init__(self):
        # Canvas Frame with dynamic sizing
        self.canvas_frame = customtkinter.CTkFrame(
            self.tabview.tab("Canvas"),
            fg_color="transparent",
        )
        self.canvas_frame.grid(
            row=1, column=0, columnspan=3, sticky="nsew", padx=10, pady=10
        )
        self.canvas_frame.grid_columnconfigure(0, weight=1)
        self.canvas_frame.grid_rowconfigure(0, weight=1)

        # Create canvas with dynamic sizing
        self.canvas = customtkinter.CTkCanvas(
            self.canvas_frame,
            bg="white",
            cursor="circle",
        )
        self.canvas.place(relx=0.5, rely=0.5, anchor="center", width=1280, height=720)

        # Bind resize event
        self.bind("<Configure>", self.on_window_resize)

        # Canvas Mouse Events
        self.canvas.bind("<Button-1>", self.canvas_mouse_down)
        self.canvas.bind("<ButtonRelease-1>", self.canvas_mouse_release)
        self.canvas.bind("<Motion>", self.mouse_move)

        # Create transform controls container but don't show it initially
        self.transform_controls = customtkinter.CTkFrame(self.tabview.tab("Canvas"))

        # Create transform mode buttons
        self.transform_mode = tkinter.StringVar(value="move")

        self.move_btn = customtkinter.CTkButton(
            self.transform_controls,
            text="Move",
            width=100,
            command=lambda: self.set_transform_mode("move"),
            fg_color="#4477AA",
        )
        self.move_btn.grid(row=0, column=0, padx=5, pady=5)

        self.scale_btn = customtkinter.CTkButton(
            self.transform_controls,
            text="Scale",
            width=100,
            command=lambda: self.set_transform_mode("scale"),
            fg_color="transparent",
        )
        self.scale_btn.grid(row=0, column=1, padx=5, pady=5)

        # Generation and Saving Buttons
        self.prompt_entry = customtkinter.CTkEntry(
            self.tabview.tab("Canvas"),
            placeholder_text="Prompt to guide image generation...",
        )
        self.prompt_entry.grid(
            row=2, column=0, padx=(20, 20), pady=(10, 10), sticky="ew"
        )
        self.generate_ai_image_btn = customtkinter.CTkButton(
            master=self.tabview.tab("Canvas"),
            fg_color="transparent",
            border_width=2,
            text="Generated AI Image",
            text_color=("gray10", "#DCE4EE"),
            command=self.generate_ai_image,
        )
        self.generate_ai_image_btn.grid(
            row=2, column=1, padx=(20, 20), pady=(20, 20), sticky="ew"
        )
        self.save_canvas = customtkinter.CTkButton(
            master=self.tabview.tab("Canvas"),
            fg_color="transparent",
            border_width=2,
            text="Save Drawing",
            text_color=("gray10", "#DCE4EE"),
            command=self.canvas_save_png,
        )
        self.save_canvas.grid(
            row=2, column=2, padx=(20, 20), pady=(20, 20), sticky="ew"
        )

        # Add layer panel frame
        self.layer_panel = customtkinter.CTkFrame(
            self.tabview.tab("Canvas"), corner_radius=0
        )
        self.layer_panel.grid(row=0, column=3, rowspan=3, sticky="nsew", padx=5, pady=5)
        self.layer_panel.grid_columnconfigure(0, weight=1)
        self.layer_panel.grid_rowconfigure(1, weight=1)

        # Add layer panel label
        self.layer_panel_label = customtkinter.CTkLabel(
            self.layer_panel,
            text="Layers",
            font=customtkinter.CTkFont(size=16, weight="bold"),
        )
        self.layer_panel_label.grid(row=0, column=0, pady=5, padx=5)

        # Add scrollable frame for layers
        self.layer_container = customtkinter.CTkScrollableFrame(
            self.layer_panel,
        )
        self.layer_container.grid(row=1, column=0, pady=5, padx=5, sticky="nsew")
