"""
Script to download required models for face recognition.

Downloads:
- Cascade classifier
- dlib face recognition model
- Shape predictor model
"""

import os
import urllib.request
import bz2
import shutil
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model paths
MODELS_DIR = "/app/models"
CASCADE_PATH = os.path.join(MODELS_DIR, "haarcascade_frontalface_default.xml")
DLIB_FACE_RECOGNITION_MODEL_PATH = os.path.join(MODELS_DIR, "dlib_face_recognition_resnet_model_v1.dat")
DLIB_SHAPE_PREDICTOR_PATH = os.path.join(MODELS_DIR, "shape_predictor_68_face_landmarks.dat")

# Model URLs
CASCADE_URL = "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml"
DLIB_FACE_RECOGNITION_MODEL_URL = "https://github.com/davisking/dlib-models/raw/master/dlib_face_recognition_resnet_model_v1.dat.bz2"
DLIB_SHAPE_PREDICTOR_URL = "https://github.com/davisking/dlib-models/raw/master/shape_predictor_68_face_landmarks.dat.bz2"

def download_file(url: str, output_path: str) -> None:
    """Download a file from URL."""
    try:
        logger.info(f"Downloading {url} to {output_path}")
        urllib.request.urlretrieve(url, output_path)
        logger.info(f"Successfully downloaded {output_path}")
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        raise

def extract_bz2(input_path: str, output_path: str) -> None:
    """Extract a bz2 file."""
    try:
        logger.info(f"Extracting {input_path} to {output_path}")
        with bz2.BZ2File(input_path, 'rb') as source, open(output_path, 'wb') as dest:
            shutil.copyfileobj(source, dest)
        logger.info(f"Successfully extracted {output_path}")
        # Remove bz2 file
        os.remove(input_path)
    except Exception as e:
        logger.error(f"Failed to extract {input_path}: {e}")
        raise

def main():
    """Main function to download and prepare models."""
    try:
        # Create models directory
        os.makedirs(MODELS_DIR, exist_ok=True)
        logger.info(f"Created models directory at {MODELS_DIR}")

        # Download cascade classifier
        if not os.path.exists(CASCADE_PATH):
            download_file(CASCADE_URL, CASCADE_PATH)

        # Download and extract dlib face recognition model
        if not os.path.exists(DLIB_FACE_RECOGNITION_MODEL_PATH):
            compressed_path = DLIB_FACE_RECOGNITION_MODEL_PATH + '.bz2'
            download_file(DLIB_FACE_RECOGNITION_MODEL_URL, compressed_path)
            extract_bz2(compressed_path, DLIB_FACE_RECOGNITION_MODEL_PATH)

        # Download and extract shape predictor model
        if not os.path.exists(DLIB_SHAPE_PREDICTOR_PATH):
            compressed_path = DLIB_SHAPE_PREDICTOR_PATH + '.bz2'
            download_file(DLIB_SHAPE_PREDICTOR_URL, compressed_path)
            extract_bz2(compressed_path, DLIB_SHAPE_PREDICTOR_PATH)

        logger.info("All models downloaded and prepared successfully")

    except Exception as e:
        logger.error(f"Failed to download and prepare models: {e}")
        raise

if __name__ == "__main__":
    main() 