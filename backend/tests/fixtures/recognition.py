"""Face recognition fixtures for testing."""
from typing import Any, Dict, List, Optional, Protocol
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock

# Define protocols for type hints without importing actual modules
class FaceRecognitionSystem(Protocol):
    """Protocol for face recognition system."""
    async def initialize(self) -> None: ...
    async def process_image(self, image: Any) -> Any: ...
    async def add_face(self, face_id: str, image: Any, metadata: Optional[Dict] = None) -> None: ...
    async def find_matches(self, image: Any, top_k: int = 5) -> List[Any]: ...
    async def remove_face(self, face_id: str) -> bool: ...
    async def clear(self) -> None: ...
    async def cleanup(self) -> None: ...

class FaceMatcher(Protocol):
    """Protocol for face matcher."""
    async def add_face(self, face_id: str, encoding: Any, metadata: Optional[Dict] = None) -> None: ...
    async def find_matches(self, encoding: Any, top_k: int = 5) -> List[Any]: ...
    async def remove_face(self, face_id: str) -> bool: ...
    async def clear(self, face_id: str) -> None: ...

class VideoProcessor(Protocol):
    """Protocol for video processor."""
    async def process_frame(self, frame: Any) -> Any: ...

@pytest_asyncio.fixture
async def setup_recognition_env():
    """Set up face recognition test environment."""
    with patch("src.core.face_recognition.face_detection.dlib.get_frontal_face_detector") as mock_detector:
        mock_detector.return_value = MagicMock()
        with patch("src.core.face_recognition.face_detection.dlib.shape_predictor") as mock_predictor:
            mock_predictor.return_value = MagicMock()
            with patch("src.core.face_recognition.face_recognition.FaceRecognitionSystem") as mock_system:
                mock_system.return_value = AsyncMock()
                with patch("src.core.face_recognition.face_recognition.FaceMatcher") as mock_matcher:
                    mock_matcher.return_value = AsyncMock()
                    with patch("src.core.face_recognition.video_processor.VideoProcessor") as mock_processor:
                        mock_processor.return_value = AsyncMock()
                        with patch("src.core.face_recognition.face_detection.FaceDetector") as mock_detector:
                            mock_detector.return_value = AsyncMock()
                            with patch("src.core.face_recognition.face_encoding.FaceEncoder") as mock_encoder:
                                mock_encoder.return_value = AsyncMock()
                                with patch("src.core.face_recognition.anti_spoofing.AntiSpoofing") as mock_anti_spoofing:
                                    mock_anti_spoofing.return_value = AsyncMock()
                                    yield

@pytest_asyncio.fixture
async def face_recognition_system(setup_recognition_env):
    """Create a mock face recognition system."""
    system = AsyncMock()
    system.initialize = AsyncMock()
    system.process_image = AsyncMock()
    system.add_face = AsyncMock()
    system.find_matches = AsyncMock()
    system.remove_face = AsyncMock()
    system.clear = AsyncMock()
    system.cleanup = AsyncMock()
    return system

@pytest_asyncio.fixture
async def face_matcher(setup_recognition_env):
    """Create a mock face matcher."""
    matcher = AsyncMock()
    matcher.add_face = AsyncMock()
    matcher.find_matches = AsyncMock()
    matcher.remove_face = AsyncMock()
    matcher.clear = AsyncMock()
    return matcher

@pytest_asyncio.fixture
async def video_processor(setup_recognition_env):
    """Create a mock video processor."""
    processor = AsyncMock()
    processor.process_frame = AsyncMock()
    return processor

@pytest_asyncio.fixture
async def face_detector(setup_recognition_env):
    """Create a mock face detector."""
    detector = AsyncMock()
    detector.detect_faces = AsyncMock()
    return detector

@pytest_asyncio.fixture
async def face_encoder(setup_recognition_env):
    """Create a mock face encoder."""
    encoder = AsyncMock()
    encoder.encode_face = AsyncMock()
    return encoder

@pytest_asyncio.fixture
async def anti_spoofing(setup_recognition_env):
    """Create a mock anti-spoofing system."""
    anti_spoofing = AsyncMock()
    anti_spoofing.analyze_frame = AsyncMock()
    anti_spoofing.get_landmarks = AsyncMock()
    anti_spoofing.is_live_face = AsyncMock()
    return anti_spoofing 