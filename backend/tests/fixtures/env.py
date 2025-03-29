"""Environment setup for testing."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def setup_test_env():
    """Set up test environment variables and paths."""
    # Set test environment and load test environment variables
    os.environ["TESTING"] = "true"
    load_dotenv(Path(__file__).parent.parent.parent / '.env.test', override=True)

    # Add backend and backend/src to Python path
    backend_dir = str(Path(__file__).parent.parent.parent)
    backend_src = str(Path(__file__).parent.parent.parent / "src")
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    if backend_src not in sys.path:
        sys.path.insert(0, backend_src)

    # Set testing environment variables
    os.environ["MODEL_PATH"] = "test_models"
    os.environ["GPU_DEVICE"] = "cuda:0"
    os.environ["FACE_RECOGNITION_MODEL"] = "test_face_model"
    os.environ["FACE_DETECTION_MODEL"] = "test_detection_model"
    os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"  # Disable oneDNN optimizations
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"  # Reduce TensorFlow logging
    os.environ["PYTHONPATH"] = f"{backend_dir}{os.pathsep}{backend_src}"
    
    # Set model paths for testing
    test_models_dir = Path(__file__).parent.parent / "test_models"
    test_models_dir.mkdir(exist_ok=True)
    
    # Create dummy model files
    shape_predictor_path = test_models_dir / "shape_predictor_68_face_landmarks.dat"
    shape_predictor_path.touch()
    
    # Set absolute paths for model files
    os.environ["SHAPE_PREDICTOR_MODEL"] = str(shape_predictor_path.absolute())
    os.environ["MODELS_DIR"] = str(test_models_dir.absolute())
    os.environ["APP_MODELS_DIR"] = str(test_models_dir.absolute())  # For /app/models path 