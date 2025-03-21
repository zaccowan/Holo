import customtkinter
from tkinter import colorchooser
from ...tools.tool_manager import ToolManager
from ...config.settings import GuiSettings


class Sidebar(customtkinter.CTkFrame):
    def __init__(self, master, tool_manager):
        super().__init__(master, width=GuiSettings.SIDEBAR_WIDTH, corner_radius=0)
        self.tool_manager = tool_manager
        self._setup_ui()

    def _setup_ui(self):
        self.grid_rowconfigure(5, weight=1)

        # Logo
        self.logo_label = customtkinter.CTkLabel(
            self, text="Holo Tools", font=customtkinter.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Color selector
        self.color_label = customtkinter.CTkLabel(
            self,
            text=f"Element Color: {self.tool_manager.hex_color}",
            fg_color=self.tool_manager.hex_color,
            font=("Arial", 12),
            padx=20,
            pady=5,
            corner_radius=5,
            cursor="hand2",
        )
        self.color_label.bind("<Button-1>", self.choose_color)
        self.color_label.grid(row=2, column=0, rowspan=2, padx=20, pady=(5, 50))

        # Size control
        self._setup_size_controls()
        self._setup_tool_radiobuttons()

    def choose_color(self, event):
        color_code = colorchooser.askcolor(title="Choose color")
        if color_code:
            self.tool_manager.set_color(color_code[1])
            self.color_label.configure(
                text=f"Element Color: {self.tool_manager.hex_color}",
                fg_color=self.tool_manager.hex_color,
            )

    def _setup_size_controls(self):
        """Setup element size controls"""
        self.element_size_label = customtkinter.CTkLabel(
            self,
            text=f"Element Size: {self.tool_manager.element_size}",
            font=("Arial", 12),
            pady=10,
        )
        self.element_size_label.grid(
            row=3, column=0, padx=(20, 10), pady=(10, 0), sticky="nsw"
        )

        self.element_size_slider = customtkinter.CTkSlider(
            self,
            from_=1,
            to=100,
            number_of_steps=100,
            command=self.tool_manager.set_element_size,
            progress_color="#4477AA",
        )
        self.element_size_slider.grid(row=4, column=0, padx=(20, 10), pady=(0, 10))
