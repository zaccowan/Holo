import replicate
import base64
import cv2
from PIL import Image, ImageTk
from ..config.settings import AISettings


class ImageGenerator:
    def __init__(self):
        self.model_id = AISettings.MODEL_ID
        self.default_params = AISettings.DEFAULT_PARAMS
        self.default_suffix_prompt = AISettings.DEFAULT_SUFFIX_PROMPT
        self.default_negative_prompt = AISettings.DEFAULT_NEGATIVE_PROMPT

    def generate_image(self, input_image_path, prompt, callback=None):
        """Generate an AI image from input sketch"""
        with open(input_image_path, "rb") as file:
            data = base64.b64encode(file.read()).decode("utf-8")
            image = f"data:application/octet-stream;base64,{data}"

        # Merge parameters with user input
        params = self.default_params.copy()
        params.update(
            {
                "image": image,
                "prompt": prompt,
                "suffix_prompt": self.default_suffix_prompt,
                "negative_prompt": self.default_negative_prompt,
            }
        )

        # Run the model
        output = replicate.run(self.model_id, input=params)

        # Save and process outputs
        generated_images = []
        for index, item in enumerate(output):
            output_path = f"output_{index}.png"
            with open(output_path, "wb") as file:
                file.write(item.read())
            generated_images.append(output_path)

        # Convert first image for display
        if generated_images:
            ai_gen_image = cv2.imread(generated_images[0])
            ai_gen_image = Image.fromarray(ai_gen_image)
            if callback:
                callback(ai_gen_image)
            return generated_images[0]

        return None

    def preview_input(self, input_image_path):
        """Show the input sketch"""
        cv2.imshow("Input Sketch", cv2.imread(input_image_path))
