"""Face recognition test fixtures."""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock

@pytest_asyncio.fixture
async def face_recognition_system():
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
async def face_matcher():
    """Create a mock face matcher."""
    matcher = AsyncMock()
    matcher.add_face = AsyncMock()
    matcher.find_matches = AsyncMock()
    matcher.remove_face = AsyncMock()
    matcher.clear = AsyncMock()
    return matcher

@pytest_asyncio.fixture
async def video_processor():
    """Create a mock video processor."""
    processor = AsyncMock()
    processor.process_frame = AsyncMock()
    return processor

@pytest_asyncio.fixture
async def face_detector():
    """Create a mock face detector."""
    detector = AsyncMock()
    detector.detect_faces = AsyncMock()
    return detector

@pytest_asyncio.fixture
async def face_encoder():
    """Create a mock face encoder."""
    encoder = AsyncMock()
    encoder.encode_face = AsyncMock()
    return encoder

@pytest_asyncio.fixture
async def anti_spoofing():
    """Create a mock anti-spoofing system."""
    anti_spoofing = AsyncMock()
    anti_spoofing.analyze_frame = AsyncMock()
    anti_spoofing.get_landmarks = AsyncMock()
    anti_spoofing.is_live_face = AsyncMock()
    return anti_spoofing 