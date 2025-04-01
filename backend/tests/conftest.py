"""Test configuration and shared fixtures."""
ut import os
import sys
from pathlib import Path

# Set up test environment before any imports
os.environ["TESTING"] = "true"
os.environ["MODEL_PATH"] = str(Path(__file__).parent / "models")
os.environ["GPU_DEVICE"] = "cpu"
os.environ["FACE_RECOGNITION_MODEL"] = "hog"
os.environ["FACE_DETECTION_MODEL"] = "hog"
os.environ["FACE_ENCODING_MODEL"] = "hog"
os.environ["ANTI_SPOOFING_MODEL"] = "hog"

# Add backend and backend/src to Python path
backend_dir = str(Path(__file__).parent.parent)
backend_src = str(Path(__file__).parent.parent / "src")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if backend_src not in sys.path:
    sys.path.insert(0, backend_src)

# Set Python path
os.environ["PYTHONPATH"] = f"{backend_dir}{os.pathsep}{backend_src}"

# Import dependencies
import pytest
import pytest_asyncio
from dotenv import load_dotenv

# Load test environment variables
load_dotenv(Path(__file__).parent / '.env.test', override=True)

# Import mock dlib before any other imports
from tests.fixtures.mock_dlib import mock_dlib

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

# Set up asyncio mode
pytest_asyncio.mode = "auto"
pytest_asyncio.asyncio_default_fixture_loop_scope = "function"

@pytest.fixture
def test_data_dir():
    """Get the test data directory."""
    return Path(__file__).parent / "data"

@pytest_asyncio.fixture
async def client():
    """Create a test client."""
    from src.main import app
    from httpx import AsyncClient
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture(autouse=True)
async def setup_recognition():
    """Setup face recognition for tests."""
    from src.core.config.settings import get_settings
    settings = get_settings()
    
    # Store original settings
    original_enabled = settings.ENABLE_FACE_RECOGNITION
    original_gpu = settings.USE_GPU
    original_testing = settings.TESTING
    
    # Enable face recognition in test environment
    settings.ENABLE_FACE_RECOGNITION = True
    settings.USE_GPU = False
    settings.TESTING = True
    
    # Initialize face recognition system
    from src.core.face_recognition import FaceRecognitionSystem
    recognition = FaceRecognitionSystem()
    
    try:
        await recognition.initialize()
        yield
    finally:
        # Ensure cleanup happens even if setup fails
        if hasattr(recognition, 'cleanup'):
            await recognition.cleanup()
        # Clear any remaining caches
        if hasattr(recognition, '_encoding_cache'):
            recognition._encoding_cache.clear()
        # Force garbage collection
        import gc
        gc.collect()
        
        # Restore original settings
        settings.ENABLE_FACE_RECOGNITION = original_enabled
        settings.USE_GPU = original_gpu
        settings.TESTING = original_testing 