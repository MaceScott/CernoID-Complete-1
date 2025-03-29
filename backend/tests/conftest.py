"""Test configuration."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Set up test environment before any imports
os.environ["TESTING"] = "true"
load_dotenv(Path(__file__).parent / '.env.test', override=True)

# Add backend and backend/src to Python path
backend_dir = str(Path(__file__).parent.parent)
backend_src = str(Path(__file__).parent.parent / "src")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if backend_src not in sys.path:
    sys.path.insert(0, backend_src)

# Set Python path
os.environ["PYTHONPATH"] = f"{backend_dir}{os.pathsep}{backend_src}"

# Import mock dlib before any other imports
from .fixtures.mock_dlib import mock_dlib

# Set up test environment variables
os.environ["MODEL_PATH"] = str(Path(__file__).parent / "models")
os.environ["GPU_DEVICE"] = "cpu"
os.environ["FACE_RECOGNITION_MODEL"] = "hog"
os.environ["FACE_DETECTION_MODEL"] = "hog"
os.environ["FACE_ENCODING_MODEL"] = "hog"
os.environ["ANTI_SPOOFING_MODEL"] = "hog"

# Create test models directory
test_models_dir = Path(__file__).parent / "models"
test_models_dir.mkdir(exist_ok=True)

# Create dummy shape predictor model file
shape_predictor_path = test_models_dir / "shape_predictor_68_face_landmarks.dat"
if not shape_predictor_path.exists():
    shape_predictor_path.touch()

# Set absolute paths for models
os.environ["SHAPE_PREDICTOR_MODEL"] = str(shape_predictor_path)
os.environ["FACE_RECOGNITION_MODEL_PATH"] = str(test_models_dir / "face_recognition_model.h5")
os.environ["FACE_DETECTION_MODEL_PATH"] = str(test_models_dir / "face_detection_model.h5")
os.environ["FACE_ENCODING_MODEL_PATH"] = str(test_models_dir / "face_encoding_model.h5")
os.environ["ANTI_SPOOFING_MODEL_PATH"] = str(test_models_dir / "anti_spoofing_model.h5") 