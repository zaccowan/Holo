import base64
import os
from tkinter import filedialog

import cv2
import replicate

import base64
import os
import tkinter
import customtkinter
from tkinter import filedialog
from PIL import ImageGrab, Image, ImageTk


# Imports for hand tracking and mouse manipulation
import math
import cv2

# General Imports
import threading

## Import for AI Image Generation
import replicate


################################
# Canvas Drawing Events
################################


class CanvasSavingFunctions:
    def __init__(self):
        pass

    def generate_ai_image(self):
        self.canvas_save_png()
        input_image_path = self.file_path
        prompt = self.prompt_entry.get()
        cv2.imshow("Input Sketch", cv2.imread(input_image_path))
        print(prompt)

        def run_replicate():
            with open(input_image_path, "rb") as file:
                data = base64.b64encode(file.read()).decode("utf-8")
                image = f"data:application/octet-stream;base64,{data}"

            replicate.Client(api_token=os.environ["REPLICATE_API_TOKEN"])

            if self.ai_model.get() == "Sketch to Image":
                output = replicate.run(
                    "qr2ai/outline:6f713aeb58eb5034ad353de02d7dd56c9efa79f2214e6b89a790dad8ca67ef49",
                    input={
                        "seed": 0,
                        "image": image,
                        "width": 1280,
                        "height": 720,
                        "prompt": prompt,
                        "sampler": "Euler a",
                        "blur_size": 3,
                        "use_canny": False,
                        "lora_input": "",
                        "lora_scale": "",
                        "kernel_size": 3,
                        "num_outputs": 1,
                        "sketch_type": "HedPidNet",
                        "suffix_prompt": "Imagine the harmonious blend of graceful forms and cosmic elegance, where each curve and line tells a story amidst the celestial backdrop, captured in a luxurious interplay of dark and light hues.",
                        "guidance_scale": 7.5,
                        "weight_primary": 0.7,
                        "generate_square": False,
                        "negative_prompt": "worst quality, low quality, low resolution, blurry, ugly, disfigured, uncrafted, filled ring, packed ring, cross, star, distorted, stagnant, watermark",
                        "weight_secondary": 0.6,
                        "erosion_iterations": 2,
                        "dilation_iterations": 1,
                        "num_inference_steps": 35,
                        "adapter_conditioning_scale": 0.9,
                    },
                )
            elif self.ai_model.get() == "t2i-adapter-sdxl-sketch":
                output = replicate.run(
                    "adirik/t2i-adapter-sdxl-sketch:3a14a915b013decb6ab672115c8bced7c088df86c2ddd0a89433717b9ec7d927",
                    input={
                        "image": image,
                        "prompt": prompt,
                        "scheduler": "K_EULER_ANCESTRAL",
                        "num_samples": 1,
                        "guidance_scale": 7.5,
                        "negative_prompt": "extra digit, fewer digits, cropped, worst quality, low quality, glitch, deformed, mutated, ugly, disfigured",
                        "num_inference_steps": 30,
                        "adapter_conditioning_scale": 0.9,
                        "adapter_conditioning_factor": 1,
                    },
                )
            else:  # T2I Adapter SDXL Sketch
                output = replicate.run(
                    "black-forest-labs/flux-schnell",
                    input={
                        "prompt": prompt,
                        "megapixels": "1",
                        "num_outputs": 1,
                        "aspect_ratio": "16:9",
                        "output_format": "png",
                        "output_quality": 80,
                        "num_inference_steps": 4,
                    },
                )

            # Rest of the function remains the same
            for index, item in enumerate(output):
                with open(f"output_{index}.png", "wb") as file:
                    file.write(item.read())

            if self.ai_model.get() == "t2i-adapter-sdxl-sketch":
                self.ai_gen_image = cv2.imread("output_1.png")
            else:
                self.ai_gen_image = cv2.imread("output_0.png")

            self.ai_gen_image = cv2.cvtColor(self.ai_gen_image, cv2.COLOR_BGR2RGB)
            self.ai_gen_image = Image.fromarray(self.ai_gen_image)
            ai_photo_image = ImageTk.PhotoImage(self.ai_gen_image)
            self.gen_ai_image_label.configure(text="")
            self.gen_ai_image_label.ai_photo_image = ai_photo_image
            self.gen_ai_image_label.configure(image=ai_photo_image)
            self.gen_ai_image_label.configure(bg_color="black")

            # Store the path to the generated image
            self.ai_generated_image_path = "output_0.png"

            # Enable the copy to canvas button
            self.copy_to_canvas_btn.configure(state="normal")

        replicate_thread = threading.Thread(target=run_replicate)
        replicate_thread.start()

    def copy_ai_image_to_canvas(self):
        """Copy the AI-generated image to the canvas and switch to Canvas tab"""
        # Switch to Canvas tab first
        self.tabview.set("Canvas")

        # Proceed with copying the image
        if hasattr(self, "ai_generated_image_path") and os.path.exists(
            self.ai_generated_image_path
        ):
            # Get current canvas dimensions
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            # Calculate center position of canvas
            x_center = canvas_width / 2
            y_center = canvas_height / 2

            # Place image at the center of canvas
            self.place_image(self.ai_generated_image_path, x_center, y_center)

    def canvas_save_png(self):
        self.canvas.delete("temp_bbox")
        self.canvas.delete("temp_rect")
        self.file_path = filedialog.asksaveasfilename(
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
                self.canvas.winfo_rootx() + self.canvas.winfo_width() - 4,
                self.canvas.winfo_rooty() + self.canvas.winfo_height() - 4,
            )
        ).save(self.file_path)
