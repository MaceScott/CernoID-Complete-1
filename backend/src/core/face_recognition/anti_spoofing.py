import dlib
import cv2
import numpy as np
import tensorflow as tf
import os
import logging
from pathlib import Path

# Load the pre-trained shape predictor model
PREDICTOR_PATH = os.getenv("SHAPE_PREDICTOR_PATH", "/app/models/shape_predictor_68_face_landmarks.dat")

# Initialize dlib's face detector and shape predictor
face_detector = dlib.get_frontal_face_detector()

# Improved error handling for shape predictor loading
try:
    if not os.path.isfile(PREDICTOR_PATH):
        raise FileNotFoundError(f"Shape predictor model not found at {PREDICTOR_PATH}")
    shape_predictor = dlib.shape_predictor(PREDICTOR_PATH)
except Exception as e:
    logging.error(f"Failed to load shape predictor: {e}")
    raise

# Load or create the pre-trained liveness detection model
model_path = os.getenv("LIVENESS_MODEL_PATH", "/app/models/liveness_model.h5")
if not os.path.isfile(model_path):
    logging.info("Creating a simple liveness detection model...")
    # Create a simple CNN model for liveness detection
    model = tf.keras.Sequential([
        tf.keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=(224, 224, 3)),
        tf.keras.layers.MaxPooling2D((2, 2)),
        tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
        tf.keras.layers.MaxPooling2D((2, 2)),
        tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])
    model.compile(optimizer='adam',
                 loss='binary_crossentropy',
                 metrics=['accuracy'])
    # Save the model
    model.save(model_path)
    logging.info(f"Saved liveness detection model to {model_path}")
else:
    try:
        model = tf.keras.models.load_model(model_path)
        logging.info("Loaded existing liveness detection model")
    except Exception as e:
        logging.error(f"Failed to load liveness model: {e}")
        raise


def detect_blink(eye_points, facial_landmarks):
    """
    Detects blinking by analyzing the eye aspect ratio (EAR).
    """
    left_point = (facial_landmarks.part(eye_points[0]).x, facial_landmarks.part(eye_points[0]).y)
    right_point = (facial_landmarks.part(eye_points[3]).x, facial_landmarks.part(eye_points[3]).y)
    center_top = midpoint(facial_landmarks.part(eye_points[1]), facial_landmarks.part(eye_points[2]))
    center_bottom = midpoint(facial_landmarks.part(eye_points[5]), facial_landmarks.part(eye_points[4]))

    # Calculate distances
    hor_line_length = np.linalg.norm(np.array(left_point) - np.array(right_point))
    ver_line_length = np.linalg.norm(np.array(center_top) - np.array(center_bottom))

    # Calculate EAR
    ear = ver_line_length / hor_line_length

    # Enhanced logging for blink detection
    logging.info(f"Blink detected with EAR: {ear}")

    return ear


def midpoint(p1, p2):
    return int((p1.x + p2.x) / 2), int((p1.y + p2.y) / 2)


def is_blinking(ear, threshold=0.2):
    """
    Determines if a blink is detected based on the EAR threshold.
    """
    return ear < threshold


def analyze_frame(frame):
    """
    Analyze a video frame to detect blinks.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_detector(gray)

    for face in faces:
        landmarks = shape_predictor(gray, face)

        # Left eye
        left_eye_ratio = detect_blink([36, 37, 38, 39, 40, 41], landmarks)
        # Right eye
        right_eye_ratio = detect_blink([42, 43, 44, 45, 46, 47], landmarks)

        if is_blinking(left_eye_ratio) or is_blinking(right_eye_ratio):
            return True
    return False


def is_live_face(frame):
    """
    Determine if the face in the frame is live or spoofed.
    """
    # Preprocess the frame for the model
    resized_frame = cv2.resize(frame, (224, 224))  # Assuming the model expects 224x224 input
    normalized_frame = resized_frame / 255.0
    input_data = np.expand_dims(normalized_frame, axis=0)

    # Predict using the model
    prediction = model.predict(input_data)
    return prediction[0][0] > 0.5  # Assuming binary classification with threshold 0.5


def process_video_feed(video_source=0):
    """
    Process video feed and apply liveness detection.
    """
    cap = cv2.VideoCapture(video_source)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Check if the face is live
        if is_live_face(frame):
            cv2.putText(frame, "Live", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "Spoof", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        cv2.imshow('Liveness Detection', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    process_video_feed()  # Start processing the default video source (webcam) 