import sys
import os
import yaml
import numpy as np
from pathlib import Path
import traceback
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ensure the project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Load config.yaml
config_path = os.path.abspath("config/config.yaml")
if not os.path.exists(config_path):
    raise FileNotFoundError(f"Configuration file not found at {config_path}")
with open(config_path, "r") as f:
    try:
        config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing configuration file: {e}")

# Extract configuration values
IMAGE_FOLDER = config.get("IMAGE_FOLDER")
if not IMAGE_FOLDER:
    raise ValueError("IMAGE_FOLDER is not defined in the configuration file.")
input_folder = Path(IMAGE_FOLDER)
if not input_folder.is_dir():
    raise NotADirectoryError(f"Input folder does not exist or is not a directory: {input_folder}")

# Import encode_faces correctly
from app.face_recognition.face_encoding import encode_faces

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_image(image_path):
    try:
        face_encodings = encode_faces(str(image_path))
        if face_encodings:
            logger.info(f"Successfully processed {image_path}")
            return image_path.name, face_encodings[0].tolist()
        else:
            logger.warning(f"No face detected in {image_path}")
            return None
    except Exception as e:
        logger.error(f"Error processing {image_path}: {e}")
        return None

def extract_embeddings(image_folder, output_file):
    """
    Extract face embeddings from all images in the specified folder and save them to a file.
    Args:
        image_folder (str): Path to folder containing images.
        output_file (str): Output file path to save embeddings.
    """
    embeddings = {}
    VALID_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp')
    images = [Path(image_folder) / f for f in os.listdir(image_folder) if f.lower().endswith(VALID_EXTENSIONS)]

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(process_image, image): image for image in images}
        for future in as_completed(futures):
            result = future.result()
            if result:
                image_name, encoding = result
                embeddings[image_name] = encoding

    with open(output_file, "w") as f:
        json.dump(embeddings, f)
    logger.info(f"Embeddings saved to {output_file}")


if __name__ == "__main__":
    output_file = input_folder / "embeddings.json"
    try:
        extract_embeddings(input_folder, output_file)
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()

