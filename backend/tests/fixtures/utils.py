"""Utility fixtures for testing."""
import pytest
import pytest_asyncio
import numpy as np
import cv2
import asyncio
from pathlib import Path
from httpx import AsyncClient

from src.main import create_app
from src.core.config.settings import get_settings
from src.core.monitoring import MonitoringService
from src.core.events import EventManager

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture
async def app(test_settings):
    """Create a test FastAPI application."""
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: test_settings
    yield app

@pytest_asyncio.fixture
async def client(app):
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client

@pytest.fixture(scope="session")
def test_image() -> bytes:
    """Create test image."""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    _, img_bytes = cv2.imencode('.jpg', img)
    return img_bytes.tobytes()

@pytest.fixture(scope="session")
def test_image_file(tmp_path_factory, test_image) -> Path:
    """Create test image file."""
    img_path = tmp_path_factory.mktemp("data") / "test.jpg"
    img_path.write_bytes(test_image)
    return img_path

@pytest_asyncio.fixture
async def monitoring_service() -> MonitoringService:
    """Get a test monitoring service."""
    return MonitoringService()

@pytest_asyncio.fixture
async def event_manager() -> EventManager:
    """Get a test event manager."""
    return EventManager() 