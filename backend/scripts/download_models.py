import os
import urllib.request
import logging
import bz2
from pathlib import Path
import shutil
import torch
import torch.nn as nn
import ssl

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Disable SSL verification for downloads
ssl._create_default_https_context = ssl._create_unverified_context

MODELS_DIR = Path(__file__).parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

MODELS = {
    "haarcascade_frontalface_default.xml": "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml",
    "shape_predictor_68_face_landmarks.dat": "https://github.com/davisking/dlib-models/raw/master/shape_predictor_68_face_landmarks.dat.bz2",
    "dlib_face_recognition_resnet_model_v1.dat": "https://github.com/davisking/dlib-models/raw/master/dlib_face_recognition_resnet_model_v1.dat.bz2"
}

def create_landmark_model():
    """Create a simple landmark detection model."""
    model = nn.Sequential(
        nn.Conv2d(3, 64, kernel_size=3, padding=1),
        nn.ReLU(),
        nn.MaxPool2d(2),
        nn.Conv2d(64, 128, kernel_size=3, padding=1),
        nn.ReLU(),
        nn.MaxPool2d(2),
        nn.Conv2d(128, 256, kernel_size=3, padding=1),
        nn.ReLU(),
        nn.MaxPool2d(2),
        nn.Flatten(),
        nn.Linear(256 * 20 * 20, 136)  # 68 landmarks * 2 coordinates
    )
    return model

def create_attribute_model():
    """Create a simple facial attribute analysis model."""
    model = nn.Sequential(
        nn.Conv2d(3, 64, kernel_size=3, padding=1),
        nn.ReLU(),
        nn.MaxPool2d(2),
        nn.Conv2d(64, 128, kernel_size=3, padding=1),
        nn.ReLU(),
        nn.MaxPool2d(2),
        nn.Conv2d(128, 256, kernel_size=3, padding=1),
        nn.ReLU(),
        nn.MaxPool2d(2),
        nn.Flatten(),
        nn.Linear(256 * 20 * 20, 10)  # 7 expressions + age + gender + quality
    )
    return model

def download_file(url: str, filename: str) -> None:
    """Download a file from a URL to the models directory."""
    filepath = MODELS_DIR / filename
    if filepath.exists():
        logger.info(f"File {filename} already exists, skipping download")
        return

    logger.info(f"Downloading {filename} from {url}")
    try:
        temp_path = filepath.with_suffix(filepath.suffix + '.tmp')
        compressed_path = filepath.with_suffix(filepath.suffix + '.bz2')
        
        # Download file
        urllib.request.urlretrieve(url, temp_path)

        if url.endswith('.bz2'):
            logger.info(f"Decompressing {filename}")
            # Move to .bz2 extension for clarity
            shutil.move(temp_path, compressed_path)
            
            # Decompress file
            with open(filepath, 'wb') as new_file:
                with bz2.BZ2File(compressed_path, 'rb') as file:
                    for data in iter(lambda: file.read(100 * 1024), b''):
                        new_file.write(data)
            
            # Remove compressed file
            compressed_path.unlink()
        else:
            temp_path.rename(filepath)

        logger.info(f"Successfully downloaded and processed {filename}")
    except Exception as e:
        logger.error(f"Failed to download {filename}: {e}")
        if temp_path.exists():
            temp_path.unlink()
        if compressed_path.exists():
            compressed_path.unlink()
        raise

def create_torch_models():
    """Create and save PyTorch models."""
    try:
        # Create and save landmark detection model
        landmark_path = MODELS_DIR / "face_landmarks.pt"
        if not landmark_path.exists():
            logger.info("Creating landmark detection model")
            landmark_model = create_landmark_model()
            torch.save(landmark_model, landmark_path)
            logger.info("Successfully created landmark detection model")

        # Create and save attribute analysis model
        attribute_path = MODELS_DIR / "face_attributes.pt"
        if not attribute_path.exists():
            logger.info("Creating facial attribute analysis model")
            attribute_model = create_attribute_model()
            torch.save(attribute_model, attribute_path)
            logger.info("Successfully created facial attribute analysis model")

    except Exception as e:
        logger.error(f"Failed to create PyTorch models: {e}")
        raise

def main():
    logger.info("Starting model downloads...")
    for filename, url in MODELS.items():
        if not os.path.exists(os.path.join(MODELS_DIR, filename)):
            download_file(url, filename)
        else:
            logger.info(f"{filename} already exists, skipping download")
    
    logger.info("Creating PyTorch models...")
    create_torch_models()
    
    logger.info("All models downloaded and created successfully")

if __name__ == "__main__":
    main() 