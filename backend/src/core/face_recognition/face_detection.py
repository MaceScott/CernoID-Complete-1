import dlib
import cv2
import yaml
import os
from pathlib import Path
import logging
from functools import lru_cache

logging.basicConfig(level=logging.INFO)

# Get configuration from environment variables
SHAPE_PREDICTOR_PATH = os.getenv("SHAPE_PREDICTOR_MODEL", "models/shape_predictor_68_face_landmarks.dat")
IMAGE_FOLDER = os.getenv("MODEL_PATH", "models")
DATABASE_CONFIG = {
    "url": os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db"),
    "echo": os.getenv("DATABASE_ECHO", "false").lower() == "true"
}

logger = logging.getLogger(__name__)

@lru_cache(maxsize=100)
def detect_faces(image_path):
    """
    Detect faces in an image using dlib's frontal face detector.
    """
    detector = dlib.get_frontal_face_detector()
    image = cv2.imread(image_path)
    if image is None:
        logger.error(f"Image at {image_path} not found.")
        raise FileNotFoundError(f"Image at {image_path} not found.")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)

    logger.info(f"Detected {len(faces)} faces in image {image_path}")

    for face in faces:
        x, y, w, h = face.left(), face.top(), face.right(), face.bottom()
        cv2.rectangle(image, (x, y), (w, h), (255, 0, 0), 2)

    return faces


if __name__ == "__main__":
    # Use environment variables for paths
    test_image_path = Path(IMAGE_FOLDER) / "test.jpg"
    if not test_image_path.exists():
        raise FileNotFoundError(f"Test image not found at {test_image_path}")

    try:
        faces = detect_faces(str(test_image_path))
        if len(faces) == 0:
            logging.info("No faces detected in the image.")
        else:
            logging.info(f"Detected {len(faces)} face(s).")
    except Exception as e:
        logging.error(f"Error: {e}")

