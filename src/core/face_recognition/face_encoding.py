import dlib
import cv2
import numpy as np
import yaml
import os
import logging
import faiss

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
config_path = os.getenv("CONFIG_FILE", "config/config.yaml")
if not os.path.isfile(config_path):
    raise FileNotFoundError(f"Configuration file not found at {config_path}")

try:
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
except yaml.YAMLError as e:
    raise RuntimeError(f"Error parsing YAML file: {e}")

# Validate required config keys
required_keys = ["SHAPE_PREDICTOR_PATH", "FACE_RECOGNIZER_PATH", "IMAGE_FOLDER"]
for key in required_keys:
    if key not in config:
        raise KeyError(f"Required key '{key}' is missing in configuration.")

SHAPE_PREDICTOR_PATH = config["SHAPE_PREDICTOR_PATH"]
FACE_RECOGNIZER_PATH = config["FACE_RECOGNIZER_PATH"]
IMAGE_FOLDER = config["IMAGE_FOLDER"]

# Initialize FAISS index
index = faiss.IndexFlatL2(128)  # 128 is the dimension of the face encoding


def encode_faces(image_path):
    """
    Encode faces in an image into numerical vectors.
    """
    detector = dlib.get_frontal_face_detector()
    shape_predictor = dlib.shape_predictor(SHAPE_PREDICTOR_PATH)
    face_recognizer = dlib.face_recognition_model_v1(FACE_RECOGNIZER_PATH)

    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Image at {image_path} not found.")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)
    encodings = []
    for face in faces:
        landmarks = shape_predictor(gray, face)
        encoding = np.array(face_recognizer.compute_face_descriptor(image, landmarks))
        encodings.append(encoding)
    return encodings


def add_encodings_to_index(encodings):
    """
    Add face encodings to the FAISS index.
    """
    if encodings:
        index.add(np.array(encodings, dtype='float32'))


def search_similar_faces(query_encoding, k=5):
    """
    Search for similar faces in the index.
    """
    query = np.array([query_encoding], dtype='float32')
    distances, indices = index.search(query, k)
    return distances, indices


if __name__ == "__main__":
    test_image_path = os.path.join(IMAGE_FOLDER, "test.jpg")
    if not os.path.isfile(test_image_path):
        raise FileNotFoundError(f"Test image not found at {test_image_path}")

    try:
        encodings = encode_faces(test_image_path)
        add_encodings_to_index(encodings)
        logger.info(f"Added {len(encodings)} face encoding(s) to the index.")

        # Example query
        if encodings:
            distances, indices = search_similar_faces(encodings[0])
            logger.info(f"Found similar faces at indices: {indices} with distances: {distances}")
    except Exception as e:
        logger.error(f"Error: {e}")

