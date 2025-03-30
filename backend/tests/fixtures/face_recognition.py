"""Face recognition test fixtures."""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import numpy as np

@pytest_asyncio.fixture
async def face_recognition_system():
    """Create a mock face recognition system."""
    system = AsyncMock()
    system.initialized = False
    system.initialize = AsyncMock()
    system.process_image = AsyncMock(return_value={
        'faces': [{'bbox': [0, 0, 100, 100], 'embedding': np.zeros(128)}],
        'landmarks': [[(0, 0)] * 68],
        'quality': 0.95
    })
    system.add_face = AsyncMock(return_value=True)
    system.find_matches = AsyncMock(return_value=[{
        'id': 'test_id',
        'confidence': 0.95,
        'bbox': [0, 0, 100, 100]
    }])
    system.remove_face = AsyncMock(return_value=True)
    system.clear = AsyncMock()
    system.cleanup = AsyncMock()
    return system

@pytest_asyncio.fixture
async def face_matcher():
    """Create a mock face matcher."""
    matcher = AsyncMock()
    matcher.initialized = False
    matcher.initialize = AsyncMock()
    matcher.add_face = AsyncMock(return_value=True)
    matcher.find_matches = AsyncMock(return_value=[{
        'id': 'test_id',
        'confidence': 0.95,
        'bbox': [0, 0, 100, 100]
    }])
    matcher.remove_face = AsyncMock(return_value=True)
    matcher.clear = AsyncMock()
    return matcher

@pytest_asyncio.fixture
async def video_processor():
    """Create a mock video processor."""
    processor = AsyncMock()
    processor.initialized = False
    processor.initialize = AsyncMock()
    processor.process_frame = AsyncMock(return_value={
        'faces': [{'bbox': [0, 0, 100, 100], 'embedding': np.zeros(128)}],
        'landmarks': [[(0, 0)] * 68],
        'quality': 0.95
    })
    return processor

@pytest_asyncio.fixture
async def face_detector():
    """Create a mock face detector."""
    detector = AsyncMock()
    detector.initialized = False
    detector.initialize = AsyncMock()
    detector.detect_faces = AsyncMock(return_value=[{
        'bbox': [0, 0, 100, 100],
        'confidence': 0.95,
        'landmarks': [(0, 0)] * 68
    }])
    return detector

@pytest_asyncio.fixture
async def face_encoder():
    """Create a mock face encoder."""
    encoder = AsyncMock()
    encoder.initialized = False
    encoder.initialize = AsyncMock()
    encoder.encode_face = AsyncMock(return_value=np.zeros(128))
    return encoder

@pytest_asyncio.fixture
async def anti_spoofing():
    """Create a mock anti-spoofing system."""
    anti_spoofing = AsyncMock()
    anti_spoofing.initialized = False
    anti_spoofing.initialize = AsyncMock()
    anti_spoofing.analyze_frame = AsyncMock(return_value={
        'is_live': True,
        'confidence': 0.95
    })
    anti_spoofing.get_landmarks = AsyncMock(return_value=[(0, 0)] * 68)
    anti_spoofing.is_live_face = AsyncMock(return_value=True)
    return anti_spoofing 