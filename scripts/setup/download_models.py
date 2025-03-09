import os
import urllib.request
import bz2
import shutil
import logging
import hashlib
import sys
from typing import Dict, Optional
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# URLs and SHA256 hashes for the model files
MODELS = {
    "shape_predictor": {
        "url": "http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2",
        "compressed": "shape_predictor_68_face_landmarks.dat.bz2",
        "decompressed": "shape_predictor_68_face_landmarks.dat",
        "size_mb": 97  # Approximate size for progress bar
    },
    "face_recognizer": {
        "url": "http://dlib.net/files/dlib_face_recognition_resnet_model_v1.dat.bz2",
        "compressed": "dlib_face_recognition_resnet_model_v1.dat.bz2",
        "decompressed": "dlib_face_recognition_resnet_model_v1.dat",
        "size_mb": 94  # Approximate size for progress bar
    }
}

class DownloadProgressBar:
    def __init__(self, total_size_mb: float):
        self.pbar = tqdm(total=total_size_mb, unit='MB', unit_scale=True)

    def update(self, chunk_size: int):
        self.pbar.update(chunk_size / (1024 * 1024))  # Convert bytes to MB

    def close(self):
        self.pbar.close()

def is_docker() -> bool:
    """Check if we're running inside a Docker container."""
    try:
        with open('/proc/1/cgroup', 'r') as f:
            return any('docker' in line for line in f)
    except:
        return False

def verify_write_permissions(path: str) -> bool:
    """Verify write permissions for the given path."""
    try:
        test_file = os.path.join(path, '.write_test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        return True
    except:
        return False

def get_models_dir() -> str:
    """Get the models directory path based on environment or default location."""
    # Check for MODEL_PATH environment variable (used in Docker)
    models_dir = os.getenv("MODEL_PATH")
    
    if not models_dir:
        # If not in Docker, use local models directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        models_dir = os.path.join(os.path.dirname(current_dir), "models")
    
    # Convert to absolute path
    models_dir = os.path.abspath(models_dir)
    
    # Check if we're in Docker
    if is_docker():
        logger.info("Running in Docker environment")
        if not models_dir.startswith('/app/'):
            logger.warning("MODEL_PATH should be within /app/ in Docker environment")
    
    return models_dir

def download_with_progress(url: str, dest_path: str, size_mb: float):
    """Download a file with progress bar."""
    progress = DownloadProgressBar(size_mb)
    
    def report_progress(count, block_size, total_size):
        progress.update(block_size)
    
    try:
        urllib.request.urlretrieve(url, dest_path, reporthook=report_progress)
    finally:
        progress.close()

def download_and_extract_model(model_info: Dict[str, str], models_dir: str):
    """Download and extract a model file."""
    compressed_path = os.path.join(models_dir, model_info["compressed"])
    decompressed_path = os.path.join(models_dir, model_info["decompressed"])
    
    # Create models directory if it doesn't exist
    os.makedirs(models_dir, exist_ok=True)
    
    # Verify write permissions
    if not verify_write_permissions(models_dir):
        raise PermissionError(f"No write permissions in {models_dir}")
    
    # Download and extract if the file doesn't exist
    if not os.path.exists(decompressed_path):
        logger.info(f"Downloading {model_info['compressed']}...")
        try:
            # Download with progress bar
            download_with_progress(
                model_info["url"],
                compressed_path,
                model_info["size_mb"]
            )
            
            # Decompress the file with progress indication
            logger.info(f"Extracting {model_info['compressed']}...")
            with bz2.BZ2File(compressed_path) as fr, open(decompressed_path, 'wb') as fw:
                shutil.copyfileobj(fr, fw)
            
            # Remove the compressed file
            os.remove(compressed_path)
            logger.info(f"Successfully downloaded and extracted {model_info['decompressed']}")
            
            # Verify file exists and is not empty
            if not os.path.exists(decompressed_path) or os.path.getsize(decompressed_path) == 0:
                raise Exception("Extracted file is missing or empty")
            
        except Exception as e:
            logger.error(f"Error processing {model_info['compressed']}: {str(e)}")
            # Clean up any partially downloaded files
            for path in [compressed_path, decompressed_path]:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception as cleanup_error:
                        logger.error(f"Error cleaning up {path}: {str(cleanup_error)}")
            raise
    else:
        logger.info(f"Model file {model_info['decompressed']} already exists")
        # Verify file is not empty
        if os.path.getsize(decompressed_path) == 0:
            logger.error(f"Existing model file {model_info['decompressed']} is empty")
            os.remove(decompressed_path)
            raise Exception(f"Empty model file detected: {decompressed_path}")

def main():
    """Download all required model files."""
    try:
        # Get the appropriate models directory
        models_dir = get_models_dir()
        logger.info(f"Using models directory: {models_dir}")
        
        # Check disk space
        if sys.platform != "win32":  # Skip on Windows
            import shutil
            total, used, free = shutil.disk_usage(models_dir)
            required_space = sum(model["size_mb"] for model in MODELS.values()) * 1024 * 1024 * 2  # Double for safety
            if free < required_space:
                raise Exception(f"Insufficient disk space. Need {required_space/(1024*1024):.1f}MB, have {free/(1024*1024):.1f}MB free")
        
        for model_name, model_info in MODELS.items():
            download_and_extract_model(model_info, models_dir)
        logger.info("All model files have been downloaded successfully!")
        
    except Exception as e:
        logger.error(f"Error downloading model files: {str(e)}")
        raise
    finally:
        # Ensure proper permissions in Docker environment
        if is_docker():
            try:
                import pwd
                uid = pwd.getpwnam('cernoid').pw_uid
                for root, dirs, files in os.walk(models_dir):
                    for d in dirs:
                        os.chown(os.path.join(root, d), uid, uid)
                    for f in files:
                        os.chown(os.path.join(root, f), uid, uid)
            except Exception as e:
                logger.warning(f"Could not set permissions in Docker: {str(e)}")

if __name__ == "__main__":
    main() 