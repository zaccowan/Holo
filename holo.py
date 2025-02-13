import tkinter
import tkinter.messagebox
import customtkinter
from tkinter import colorchooser, filedialog
from PIL import ImageGrab, Image
import ctypes


customtkinter.set_appearance_mode(
    "System"
)  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme(
    "dark-blue"
)  # Themes: "blue" (standard), "green", "dark-blue"


class Holo(customtkinter.CTk):
    mouse_down = False
    hex_color = "black"
    brush_size = 5

    def __init__(self):
        super().__init__()

        # configure window
        self.title("Holo")
        self.geometry(f"{1100}x{580}")
        # self.holo_logo_webp = Image.open("./images/holo_logo.webp")
        # self.holo_logo_webp.save("./images/holo_logo.png", "PNG")

        self.holo_logo = tkinter.PhotoImage(file="./images/holo_transparent_scaled.png")
        myappid = "tkinter.python.test"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        self.wm_iconbitmap("./images/holo_transparent_scaled.png")

        # holo_logo = PhotoImage.open(file="./images/holo_logo.webp")
        self.iconphoto(False, self.holo_logo)

        # configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        ################################
        ################################
        # create sidebar frame with widgets
        ################################
        ################################
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")

        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        self.logo_label = customtkinter.CTkLabel(
            self.sidebar_frame,
            text="Holo Tools",
            font=customtkinter.CTkFont(size=20, weight="bold"),
        )

        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.brush_color_btn = customtkinter.CTkButton(
            self.sidebar_frame,
            text="Edit Element Color",
            command=self.choose_color_btn,
        )
        self.brush_color_btn.grid(row=1, column=0, padx=20, pady=(10, 10))
        self.color_label = customtkinter.CTkLabel(
            self.sidebar_frame,
            text="Element Color: None",
            font=("Arial", 12),
            padx=20,
            pady=5,
            corner_radius=5,
        )
        self.color_label.bind("<Button-1>", self.choose_color_label)
        self.color_label.grid(row=2, column=0, rowspan=2, padx=20, pady=(5, 50))

        self.brush_size_label = customtkinter.CTkLabel(
            self.sidebar_frame, text="Brush Size: 5", font=("Arial", 12), pady=10
        )

        self.brush_size_label.grid(row=3, column=0, padx=(20, 10), pady=(10, 0))
        self.brush_size_slider = customtkinter.CTkSlider(
            self.sidebar_frame,
            from_=1,
            to=100,
            number_of_steps=100,
            command=self.set_brush_size,
        )
        self.brush_size_slider.grid(row=4, column=0, padx=(20, 10), pady=(0, 10))
        self.brush_size_slider

        self.appearance_mode_label = customtkinter.CTkLabel(
            self.sidebar_frame, text="Appearance Mode:", anchor="w"
        )
        self.appearance_mode_label.grid(row=6, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(
            self.sidebar_frame,
            values=["Light", "Dark", "System"],
            command=self.change_appearance_mode_event,
        )
        self.appearance_mode_optionemenu.grid(row=7, column=0, padx=20, pady=(10, 10))
        self.scaling_label = customtkinter.CTkLabel(
            self.sidebar_frame, text="UI Scaling:", anchor="w"
        )
        self.scaling_label.grid(row=8, column=0, padx=20, pady=(10, 0), sticky="sw")
        self.scaling_optionemenu = customtkinter.CTkOptionMenu(
            self.sidebar_frame,
            values=["80%", "90%", "100%", "110%", "120%"],
            command=self.change_scaling_event,
        )
        self.scaling_optionemenu.grid(row=9, column=0, padx=20, pady=(10, 20))

        # create canvas
        self.canvas = customtkinter.CTkCanvas(self, width=1920, height=1080, bg="white")
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure((2, 3, 4), weight=1)
        self.canvas.grid(row=0, column=2, columnspan=3, rowspan=3)

        self.canvas.bind("<Button-1>", self.canvas_mouse_down)
        self.canvas.bind("<ButtonRelease-1>", self.canvas_mouse_release)
        self.canvas.bind("<Motion>", self.mouse_move)

        ################################
        ################################
        # create main entry and button
        ################################
        ################################
        self.grid_columnconfigure(1, weight=1)
        self.name_entry = customtkinter.CTkEntry(
            self, placeholder_text="Generate Image from sketck prompt"
        )
        self.name_entry.grid(
            row=3, column=1, columnspan=2, padx=(20, 0), pady=(20, 20), sticky="nsew"
        )

        self.generate_ai_image_btn = customtkinter.CTkButton(
            master=self,
            fg_color="transparent",
            border_width=2,
            text="Generate AI Image",
            text_color=("gray10", "#DCE4EE"),
            command=self.generate_ai_image,
        )
        self.generate_ai_image_btn.grid(
            row=3, column=3, padx=(20, 20), pady=(20, 20), sticky="nsew"
        )

        self.save_name_btn = customtkinter.CTkButton(
            master=self,
            fg_color="transparent",
            border_width=2,
            text="Save Drawing",
            text_color=("gray10", "#DCE4EE"),
            command=self.canvas_save_png,
        )
        self.save_name_btn.grid(
            row=3, column=4, padx=(20, 20), pady=(20, 20), sticky="nsew"
        )

        # set default values
        self.appearance_mode_optionemenu.set("Dark")
        self.scaling_optionemenu.set("100%")

    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        customtkinter.set_widget_scaling(new_scaling_float)

    def choose_color_btn(self):
        self.color_code = colorchooser.askcolor(title="Choose color")
        if self.color_code:
            self.hex_color = self.color_code[1]
            self.color_label.configure(
                text=f"Element Color: {self.hex_color}", fg_color=self.hex_color
            )

    def choose_color_label(self, event):
        self.color_code = colorchooser.askcolor(title="Choose color")
        if self.color_code:
            self.hex_color = self.color_code[1]
            self.color_label.configure(
                text=f"Element Color: {self.hex_color}", fg_color=self.hex_color
            )

    def set_brush_size(self, event):
        self.brush_size = int(self.brush_size_slider.get())
        self.brush_size_label.configure(text=f"Brush Size: {self.brush_size}")

    def mouse_move(self, event):
        if self.mouse_down:
            self.canvas.create_aa_circle(
                event.x, event.y, self.brush_size, 0, str(self.hex_color)
            )

    def canvas_mouse_down(self, event):
        self.mouse_down = True

    def canvas_mouse_release(self, event):
        self.mouse_down = False

    def generate_ai_image(self):
        pass

    def canvas_save_png(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension="*.png",
            filetypes=(
                ("PNG Files", "*.png"),
                ("JPG Files", "*.jpg"),
            ),
        )
        ImageGrab.grab(
            bbox=(
                self.canvas.winfo_rootx(),
                self.canvas.winfo_rooty(),
                self.canvas.winfo_rootx() + self.canvas.winfo_width(),
                self.canvas.winfo_rooty() + self.canvas.winfo_height(),
            )
        ).save(file_path)

    def sidebar_button_event(self):
        print("sidebar_button click")


if __name__ == "__main__":
    app = Holo()
    app.mainloop()
