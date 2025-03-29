"""Face recognition tests."""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch

# Import face recognition fixtures
from .fixtures.face_recognition_conftest import (
    setup_recognition_env,
    mock_face_detector,
    mock_face_recognizer,
    mock_face_matcher,
    face_recognition_system,
    face_matcher,
    video_processor
)

@pytest.mark.asyncio
async def test_face_recognition_initialization(face_recognition_system):
    """Test face recognition system initialization."""
    await face_recognition_system.initialize()
    assert face_recognition_system.initialized

@pytest.mark.asyncio
async def test_face_matcher_initialization(face_matcher):
    """Test face matcher initialization."""
    await face_matcher.initialize()
    assert face_matcher.initialized

@pytest.mark.asyncio
async def test_video_processor_initialization(video_processor):
    """Test video processor initialization."""
    await video_processor.initialize()
    assert video_processor.initialized 