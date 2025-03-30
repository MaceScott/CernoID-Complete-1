"""Basic tests to verify test environment."""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock

# Import required fixtures
from .fixtures.db import db_session
from .fixtures.api_conftest import app, event_loop
from .fixtures.face_recognition import face_recognition_system

@pytest.mark.asyncio
async def test_async():
    """Test that async tests work."""
    assert True

@pytest.mark.asyncio
async def test_mock():
    """Test that mocks work."""
    mock = AsyncMock()
    mock.some_method.return_value = "test"
    result = await mock.some_method()
    assert result == "test"

@pytest.mark.asyncio
async def test_face_recognition_system(face_recognition_system):
    """Test that face recognition system is available."""
    assert face_recognition_system is not None
    await face_recognition_system.initialize()
    face_recognition_system.initialize.assert_called_once()

@pytest.mark.asyncio
async def test_db_session(db_session):
    """Test that database session is available."""
    assert db_session is not None

@pytest.mark.asyncio
async def test_app(app):
    """Test that FastAPI app is available."""
    assert app is not None 