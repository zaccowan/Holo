import customtkinter
import pywinstyles


def apply_win_style(self, style_name):
    pywinstyles.apply_style(self, style_name)
    pywinstyles.set_opacity(self.canvas, 1)
    pywinstyles.set_opacity(self.webcam_image_label, 1)
    pywinstyles.set_opacity(self.gen_ai_image_label, 1)


def change_appearance_mode_event(self, new_appearance_mode: str):
    customtkinter.set_appearance_mode(new_appearance_mode)
    if new_appearance_mode == "Light":
        self.apply_win_style("mica")
    elif new_appearance_mode == "Dark":
        self.apply_win_style("acrylic")
        pywinstyles.set_opacity(self, 1)


def change_scaling_event(self, new_scaling: str):
    new_scaling_float = int(new_scaling.replace("%", "")) / 100
    customtkinter.set_widget_scaling(new_scaling_float)
