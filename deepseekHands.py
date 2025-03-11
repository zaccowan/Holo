import cv2
import mediapipe as mp
import pyautogui
import math

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
)
mp_drawing = mp.solutions.drawing_utils

# Get screen size
screen_width, screen_height = pyautogui.size()

# Initialize webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

# Variables for mouse control
mouse_pressed = False
smoothing_factor = 5
x_points = []
y_points = []

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    # Flip frame horizontally for mirror effect
    # frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process frame with MediaPipe Hands
    results = hands.process(rgb_frame)
    current_click = False

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Get index and thumb landmarks
            index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]

            # Calculate distance between fingers
            distance = math.hypot(index_tip.x - thumb_tip.x, index_tip.y - thumb_tip.y)

            # Click detection (adjust threshold as needed)
            if distance < 0.05:  # Threshold for "OK" gesture
                current_click = True

            # Convert coordinates to screen position
            mouse_x = (1 - index_tip.x) * screen_width  # Flip x-axis
            mouse_y = ((index_tip.y + thumb_tip.y) / 2) * screen_height

            # Smooth mouse movement
            x_points.append(mouse_x)
            y_points.append(mouse_y)
            if len(x_points) > smoothing_factor:
                x_points.pop(0)
                y_points.pop(0)

            avg_x = sum(x_points) / len(x_points)
            avg_y = sum(y_points) / len(y_points)

            # Move mouse
            pyautogui.moveTo(avg_x, avg_y)
            # pyautogui.moveTo(mouse_x, mouse_y)

            # Draw hand landmarks (optional)
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            break  # Process only the first detected hand

    # Handle mouse click state
    if current_click != mouse_pressed:
        if current_click:
            pyautogui.mouseDown()
            mouse_pressed = True
        else:
            pyautogui.mouseUp()
            mouse_pressed = False

    # Release mouse if no hands detected
    if not results.multi_hand_landmarks and mouse_pressed:
        pyautogui.mouseUp()
        mouse_pressed = False
        x_points = []
        y_points = []

    # Display frame
    cv2.imshow("Hand Controlled Mouse", frame)

    if cv2.waitKey(5) & 0xFF == ord("q"):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
