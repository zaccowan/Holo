import tkinter
import customtkinter

from config import AI_MODELS, DEFAULT_AI_MODEL


class GenAIGUI:
    def __init__(self):
        # Generated AI Image Tab
        self.tabview.tab("Generated AI Image").columnconfigure(0, weight=1)
        self.tabview.tab("Generated AI Image").rowconfigure(
            1, weight=1
        )  # Changed from 0 to 1

        # Add model selection frame
        self.model_select_frame = customtkinter.CTkFrame(
            self.tabview.tab("Generated AI Image")
        )
        self.model_select_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        # Add model selection dropdown
        self.ai_model = tkinter.StringVar(value=DEFAULT_AI_MODEL)
        self.model_select = customtkinter.CTkOptionMenu(
            self.model_select_frame,
            values=AI_MODELS,
            variable=self.ai_model,
            width=200,
        )
        self.model_select.grid(row=0, column=0, padx=5, pady=5)

        self.gen_ai_image_label = customtkinter.CTkLabel(
            self.tabview.tab("Generated AI Image"),
            text="Waiting for AI Generated Image (this may take time)",
        )
        self.gen_ai_image_label.grid(row=1, column=0)

        # Add this where your gen_ai_image_label is created in __init__
        self.copy_to_canvas_btn = customtkinter.CTkButton(
            master=self.tabview.tab("Generated AI Image"),
            fg_color="transparent",
            border_width=2,
            text="Copy to Canvas",
            text_color=("gray10", "#DCE4EE"),
            command=self.copy_ai_image_to_canvas,
            state="disabled",  # Initially disabled until an image is generated
        )
        self.copy_to_canvas_btn.grid(
            row=2, column=0, padx=(20, 20), pady=(5, 20), sticky="ew"
        )
