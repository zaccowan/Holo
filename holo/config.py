# General settings
DEFAULT_FRAME_WIDTH = 1280
DEFAULT_FRAME_HEIGHT = 720
MIN_FRAME_WIDTH = 800
MIN_FRAME_HEIGHT = 450
ASPECT_RATIO = 16 / 9

# Mouse settings
VELOCITY_THRESHOLD_X = 7.0
VELOCITY_THRESHOLD_Y = 7.0
BASE_SLOW_FACTOR = 0.1
MIN_BOUND_SIZE = 600

# Appearance settings
DEFAULT_APPEARANCE_MODE = "System"
DEFAULT_COLOR_THEME = "./holo_theme.json"

# Tool settings
TOOL_DICT = {
    0: "Circle Brush",
    1: "Rectangle Tool",
    2: "Fill Tool",
    3: "Text Tool",
    4: "Transform Tool",
    5: "Delete Tool",
    6: "Image Tool",
    7: "Calligraphy",
}

# AI model settings
AI_MODELS = ["Sketch to Image", "Flux Schnell", "t2i-adapter-sdxl-sketch"]
DEFAULT_AI_MODEL = "Sketch to Image"
