# Holo Main Application Directory Structure

## Function Modules

### `functions/canvasMouseFunctions.py`
Handles all mouse interactions with the canvas.
Processes mouse events (clicks, drags, releases) to draw shapes, handle selections,
transform objects, and manage the active tools. Core drawing functionality implementation.

### `functions/canvasSavingFunctions.py`
Manages saving canvas content and AI image generation.
Handles exporting canvas drawings to files, generating AI images from drawings
using external APIs, and copying AI-generated images to the canvas.

### `functions/handTrackingCalibrationFunctions.py`
Manages hand tracking calibration for webcam input.
Provides functions to configure hand tracking boundaries and depth sensing,
allowing users to use hand gestures as input by calibrating to their environment.

### `functions/layerPanelFunctions.py`
Handles the layer management interface and operations.
Manages adding, selecting, deleting, and editing layers in the layer panel.
Controls layer properties like color, text attributes, and selection state.

### `functions/textFunctions.py`
Manages text-related functionality for the canvas.
Handles opening the text entry window and placing text elements on the canvas.
Works with the TextEntry component to add user-supplied text to drawings.

### `functions/toolbarFunctions.py`
Manages drawing tool functionality and element properties.
Handles tool selection, color picking, element sizing, and transform operations.
Controls the behavior of different drawing tools and object transformations.

### `functions/webcamFunctions.py`
Handles webcam capture and hand tracking for gesture control.
Manages camera initialization, processing video frames, detecting hand positions,
and translating hand movements to mouse actions for controlling the application.

### `functions/windowHelperFunctions.py`
Provides window management utilities.
Handles window appearance styles, scaling, fullscreen toggling, and
other window-related operations across the application.

<br>
<br>

## GUI Components

### `GUI/BaseGUI.py`
Defines the main application window class that handles the base UI layout.
Creates the sidebar with tool selection, the main content area, and sets up the tab structure.
Controls appearance settings, scaling, and the basic UI framework for the entire application.

### `GUI/CanvasGUI.py`
Handles the Canvas tab interface where drawing takes place.
Creates and configures the drawing canvas, transform controls for manipulating elements,
and buttons for saving/generating images. Sets up canvas event bindings.

### `GUI/GenAIGUI.py`
Manages the AI image generation tab interface.
Sets up the model selection dropdown, result display area, and controls 
for generating AI images from canvas drawings and copying them back to canvas.

### `GUI/TextEntry.py`
Creates a popup window for text entry with both keyboard and speech input.
Provides an interface for typing text or using speech recognition to add text
to the canvas. Includes speech recognition controls and text submission.

### `GUI/WebcamGUI.py`
Manages the webcam interface tab for hand tracking input.
Sets up camera selection, webcam feed display, hand tracking controls,
and bounding box configuration for using hand gestures to control the application.

<br>
<br>

## Core Files

### `holo.py`
Main entry point for the Holo application. Initializes the application by loading environment variables, 
setting up the GUI, and importing necessary modules and functions. Sets the default appearance mode 
and color theme for the application.

### `config.py` 
Contains application configuration constants including default window dimensions, appearance settings,
tool definitions, and AI model configurations.

### `holo_theme.json`
Defines the custom color theme used throughout the application.

