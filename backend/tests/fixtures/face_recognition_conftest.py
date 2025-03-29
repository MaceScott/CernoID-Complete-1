"""Face recognition test configuration."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Set up test environment before any imports
os.environ["TESTING"] = "true"
load_dotenv(Path(__file__).parent.parent / '.env.test', override=True)

# Add backend and backend/src to Python path
backend_dir = str(Path(__file__).parent.parent.parent)
backend_src = str(Path(__file__).parent.parent.parent / "src")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if backend_src not in sys.path:
    sys.path.insert(0, backend_src)

# Set model paths for testing
test_models_dir = Path(__file__).parent.parent / "test_models"
test_models_dir.mkdir(exist_ok=True)

# Set environment variables for testing
os.environ.update({
    "MODEL_PATH": str(test_models_dir),
    "GPU_DEVICE": "cuda:0",
    "FACE_RECOGNITION_MODEL": "test_face_model",
    "FACE_DETECTION_MODEL": "test_detection_model",
    "TF_ENABLE_ONEDNN_OPTS": "0",  # Disable oneDNN optimizations
    "TF_CPP_MIN_LOG_LEVEL": "2",  # Reduce TensorFlow logging
    "SHAPE_PREDICTOR_MODEL": str(test_models_dir / "shape_predictor_68_face_landmarks.dat"),
    "MODELS_DIR": str(test_models_dir.absolute()),
    "APP_MODELS_DIR": str(test_models_dir.absolute()),  # For /app/models path
    "PYTHONPATH": f"{backend_dir}{os.pathsep}{backend_src}"
})

# Now import face recognition fixtures
from .recognition import (
    setup_recognition_env,
    mock_face_detector,
    mock_face_recognizer,
    mock_face_matcher,
    face_recognition_system,
    face_matcher,
    video_processor
) 