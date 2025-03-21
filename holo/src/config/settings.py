class GuiSettings:
    WINDOW_WIDTH = 1280
    WINDOW_HEIGHT = 720
    APPEARANCE_MODE = "System"
    DEFAULT_COLOR_THEME = "dark-blue"
    SIDEBAR_WIDTH = 140
    DEFAULT_ELEMENT_SIZE = 5
    DEFAULT_HEX_COLOR = "#000000"


class CameraSettings:
    FRAME_WIDTH = 1280
    FRAME_HEIGHT = 720
    FPS = 30
    API_BACKEND = "dshow"
    SMOOTHING_WINDOW_SIZE = 5


class HandTrackingSettings:
    STATIC_IMAGE_MODE = False
    MAX_NUM_HANDS = 1
    MIN_DETECTION_CONFIDENCE = 0.7
    MIN_TRACKING_CONFIDENCE = 0.7
    CLICK_THRESHOLD = 0.05


class ToolSettings:
    TOOLS = {
        0: "Circle Brush",
        1: "Rectangle Tool",
        2: "Fill Tool",
        3: "Text Tool",
        4: "Transform Tool",
        5: "Delete Tool",
    }
    TOOL_CURSORS = {
        "Circle Brush": "circle",
        "Rectangle Tool": "tcross",
        "Fill Tool": "spraycan",
        "Text Tool": "xterm",
        "Transform Tool": "fleur",
        "Delete Tool": "X_cursor",
    }


class AISettings:
    MODEL_ID = (
        "qr2ai/outline:6f713aeb58eb5034ad353de02d7dd56c9efa79f2214e6b89a790dad8ca67ef49"
    )
    DEFAULT_PARAMS = {
        "seed": 0,
        "width": 1280,
        "height": 720,
        "sampler": "Euler a",
        "blur_size": 3,
        "use_canny": False,
        "kernel_size": 3,
        "num_outputs": 1,
        "sketch_type": "HedPidNet",
        "guidance_scale": 7.5,
        "weight_primary": 0.7,
        "generate_square": False,
        "weight_secondary": 0.6,
        "erosion_iterations": 2,
        "dilation_iterations": 1,
        "num_inference_steps": 35,
        "adapter_conditioning_scale": 0.9,
    }
    DEFAULT_SUFFIX_PROMPT = "Imagine the harmonious blend of graceful forms and cosmic elegance, where each curve and line tells a story amidst the celestial backdrop, captured in a luxurious interplay of dark and light hues."
    DEFAULT_NEGATIVE_PROMPT = "worst quality, low quality, low resolution, blurry, ugly, disfigured, uncrafted, filled ring, packed ring, cross, star, distorted, stagnant, watermark"
