import tkinter
from tkinter import Menu
import tkinter.messagebox
import tkinter.ttk
import customtkinter
from tkinter import colorchooser, filedialog
from PIL import ImageGrab, Image, ImageTk
import ctypes
import numpy as np
import cv2


customtkinter.set_appearance_mode(
    "System"
)  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme(
    "dark-blue"
)  # Themes: "blue" (standard), "green", "dark-blue"


class Holo(customtkinter.CTk):
    mouse_down = False
    hex_color = "#000000"
    brush_size = 5
    tool_dict = {0: "Circle Brush", 1: "Rectangle Tool", 2: "Fill Tool"}
    active_tool = "Circle Brush"
    mouse_active_coords = {
        "previous": None,
        "current": None,
    }

    mouse_down_canvas_coords = (0, 0)
    mouse_release_canvas_coords = (0, 0)

    cap = cv2.VideoCapture(0)

    cam_width, cam_height = 1280, 720
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_height)

    def __init__(self):
        super().__init__()

        # configure window
        self.title("Holo")
        self.geometry(f"{1280}x{720}")
        self.bind("<Escape>", lambda e: app.quit())
        self.menu_bar = Menu(self)

        file_menu = Menu(self.menu_bar, tearoff=0)
        # add menu items to the File menu
        file_menu.add_command(label="New")
        file_menu.add_command(label="Open...")
        file_menu.add_command(label="Close")
        file_menu.add_separator()

        # add Exit menu item
        file_menu.add_command(label="Exit", command=self.destroy)

        self.menu_bar.add_cascade(label="File", menu=file_menu, underline=0)
        self.configure(menu=self.menu_bar)

        self.holo_logo = tkinter.PhotoImage(file="./images/holo_transparent_scaled.png")
        myappid = "tkinter.python.test"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        self.wm_iconbitmap("./images/holo_transparent_scaled.png")

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
            text=f"Element Color: {self.hex_color}",
            fg_color=self.hex_color,
            font=("Arial", 12),
            padx=20,
            pady=5,
            corner_radius=5,
        )
        self.color_label.bind("<Button-1>", self.choose_color_label)
        self.color_label.grid(row=2, column=0, rowspan=2, padx=20, pady=(5, 50))

        self.brush_size_label = customtkinter.CTkLabel(
            self.sidebar_frame,
            text=f"Brush Size: {self.brush_size}",
            font=("Arial", 12),
            pady=10,
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

        # create radiobutton frame
        self.radiobutton_frame = customtkinter.CTkFrame(self.sidebar_frame)
        self.radiobutton_frame.grid(
            row=5, column=0, padx=(20, 20), pady=(20, 0), sticky="nsew"
        )
        self.radio_tool_var = tkinter.IntVar(value=0)
        self.radio_tool_var.trace_add("write", callback=self.set_active_tool)
        self.label_radio_group = customtkinter.CTkLabel(
            master=self.radiobutton_frame, text="Select Tool:"
        )
        self.label_radio_group.grid(
            row=0, column=0, columnspan=1, padx=10, pady=10, sticky="nsew"
        )

        self.radio_button_1 = customtkinter.CTkRadioButton(
            master=self.radiobutton_frame,
            variable=self.radio_tool_var,
            value=0,
            text="Circle Brush",
        )
        self.radio_button_1.grid(row=1, column=0, pady=10, padx=20, sticky="nsew")

        self.radio_button_2 = customtkinter.CTkRadioButton(
            master=self.radiobutton_frame,
            variable=self.radio_tool_var,
            value=1,
            text="Rectangle Tool",
        )
        self.radio_button_2.grid(row=2, column=0, pady=10, padx=20, sticky="nsew")
        self.radio_button_3 = customtkinter.CTkRadioButton(
            master=self.radiobutton_frame,
            variable=self.radio_tool_var,
            value=2,
            text="Fill Tool",
        )
        self.radio_button_3.grid(row=3, column=0, pady=10, padx=20, sticky="nsew")

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

        # Main Frame
        self.main_frame = customtkinter.CTkFrame(
            self,
            corner_radius=0,
        )
        self.main_frame.grid(row=0, rowspan=4, column=1, padx=0, pady=0, sticky="NSEW")
        self.main_ribbon = tkinter.ttk.Notebook(self.main_frame)

        # create tabview
        self.tabview = customtkinter.CTkTabview(
            self.main_frame,
            bg_color="transparent",
            fg_color="transparent",
        )
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.tabview.grid(row=0, column=0, padx=(20, 20), pady=(10, 10), sticky="NSEW")
        self.tabview.add("Canvas")
        self.tabview.add("Genrated AI Image")
        self.tabview.add("Webcam Image")

        # Canvas Tab
        self.canvas = customtkinter.CTkCanvas(
            self.tabview.tab("Canvas"),
            width=1280,
            height=720,
            bg="white",
        )
        self.tabview.tab("Canvas").grid_columnconfigure((0, 1, 2), weight=1)
        self.tabview.tab("Canvas").grid_rowconfigure(0, weight=1)
        self.canvas.grid(row=0, column=0, columnspan=3)

        self.canvas.create_line(0, 0, 50, 50, width=40)

        self.canvas.bind("<Button-1>", self.canvas_mouse_down)
        self.canvas.bind("<ButtonRelease-1>", self.canvas_mouse_release)
        self.canvas.bind("<Motion>", self.mouse_move)

        # Generated AI Image Tab

        # Webcam Tab
        self.tabview.tab("Webcam Image").columnconfigure((0, 1), weight=1)
        self.tabview.tab("Webcam Image").rowconfigure(0, weight=1)
        self.webcam_image_label = customtkinter.CTkLabel(
            self.tabview.tab("Webcam Image"), text="Webcam Image"
        )
        self.webcam_image_label.grid(row=0, column=0, columnspan=2)
        self.open_camera_btn = customtkinter.CTkButton(
            self.tabview.tab("Webcam Image"),
            text="Open Camera",
            command=self.open_camera,
        )
        self.open_camera_btn.grid(row=1, column=0)
        self.close_camera_btn = customtkinter.CTkButton(
            self.tabview.tab("Webcam Image"),
            text="Close Camera",
            state="disabled",
            command=self.close_camera,
        )
        self.close_camera_btn.grid(row=1, column=1)

        # ################################
        # ################################
        # # create main entry and button
        # ################################
        # ################################
        self.prompt_entry = customtkinter.CTkEntry(
            self.tabview.tab("Canvas"),
            placeholder_text="Prompt to guide image generation...",
        )
        self.prompt_entry.grid(
            row=1, column=0, padx=(20, 20), pady=(10, 10), sticky="ew"
        )

        self.generate_ai_image_btn = customtkinter.CTkButton(
            master=self.tabview.tab("Canvas"),
            fg_color="transparent",
            border_width=2,
            text="Generate AI Image",
            text_color=("gray10", "#DCE4EE"),
            command=self.generate_ai_image,
        )
        self.generate_ai_image_btn.grid(
            row=1, column=1, padx=(20, 20), pady=(20, 20), sticky="ew"
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
            row=1, column=2, padx=(20, 20), pady=(20, 20), sticky="ew"
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

    def set_active_tool(self, *args):
        self.active_tool = self.tool_dict.get(self.radio_tool_var.get())
        print(self.active_tool)

    def mouse_move(self, event):
        if self.mouse_down:
            self.mouse_active_coords["previous"] = self.mouse_active_coords["current"]
            self.mouse_active_coords["current"] = (event.x, event.y)
            # print(self.mouse_active_coords)
            if (
                self.mouse_active_coords["previous"]
                != self.mouse_active_coords["current"]
                and self.mouse_active_coords["previous"] != None
            ):
                x_interp_float = np.linspace(
                    self.mouse_active_coords["previous"][0],
                    self.mouse_active_coords["current"][0],
                    num=150 - self.brush_size,
                )
                y_interp_float = np.linspace(
                    self.mouse_active_coords["previous"][1],
                    self.mouse_active_coords["current"][1],
                    num=150 - self.brush_size,
                )
                x_interp = [int(x) for x in x_interp_float]
                y_interp = [int(y) for y in y_interp_float]
                match self.active_tool:
                    case "Circle Brush":
                        for index, x in enumerate(x_interp):
                            self.canvas.create_aa_circle(
                                x,
                                y_interp[index],
                                self.brush_size,
                                0,
                                str(self.hex_color),
                            )
                    case "Rectangle Tool":
                        self.canvas.create_aa_circle(
                            event.x, event.y, self.brush_size, 0, str(self.hex_color)
                        )
                    case "Fill Tool":
                        self.canvas.create_rectangle(
                            0,
                            0,
                            self.canvas.winfo_width(),
                            self.canvas.winfo_height(),
                            fill=self.hex_color,
                        )

        # elif not self.mouse_down:
        #     self.mouse_release_canvas_coords_canvas_coords = event.x, event.y
        #     print("Mouse down:", self.mouse_release_canvas_coords)

    def canvas_mouse_down(self, event):
        self.mouse_down = True
        print(self.mouse_down_canvas_coords)

    def canvas_mouse_release(self, event):
        self.mouse_down = False
        self.mouse_active_coords["previous"] = None
        self.mouse_active_coords["current"] = None

        # self.mouse_release_canvas_coords_canvas_coords = event.x, event.y
        # print("Mouse down:", self.mouse_release_canvas_coords)

    def tab_right_click(self, event):
        print("Right Click")
        self.tabview.tab("Canvas").destroy()

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

    def open_camera(self):

        if self.cap.isOpened():
            self.open_camera_btn.configure(state="disabled")
            self.close_camera_btn.configure(state="normal")

        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)

            cam_width, cam_height = 1280, 720
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_height)
            self.open_camera
            return

        # Capture the video frame by frame
        _, frame = self.cap.read()

        # Convert image from one color space to other
        opencv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)

        # Capture the latest frame and transform to image
        captured_image = Image.fromarray(opencv_image)

        # Convert captured image to photoimage
        photo_image = ImageTk.PhotoImage(image=captured_image)

        self.webcam_image_label.configure(text="")

        # Displaying photoimage in the label
        self.webcam_image_label.photo_image = photo_image

        # Configure image in the label
        self.webcam_image_label.configure(image=ImageTk.PhotoImage(captured_image))

        # Repeat the same process after every 10 seconds
        self.webcam_image_label.after(10, self.open_camera)

    def close_camera(self):
        self.open_camera_btn.configure(state="normal")
        self.close_camera_btn.configure(state="disabled")
        self.cap.release()
        cv2.destroyAllWindows()
        self.webcam_image_label.destroy()
        self.webcam_image_label = customtkinter.CTkLabel(
            self.tabview.tab("Webcam Image"), text="Webcam Image"
        )
        self.webcam_image_label.grid(row=0, column=0, columnspan=2)
        self.webcam_image_label.configure(image=None)
        self.webcam_image_label.configure(text="Webcam Image")


if __name__ == "__main__":
    app = Holo()
    app.mainloop()
