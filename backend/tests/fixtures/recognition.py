"""Fixtures for face recognition tests."""
import pytest
import pytest_asyncio
from pathlib import Path
import base64
import cv2
import numpy as np
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def test_data_dir():
    """Get the test data directory."""
    return Path(__file__).parent.parent / "data"

@pytest.fixture
def test_image():
    """Create a test image."""
    img = np.ones((480, 640, 3), dtype=np.uint8) * 255
    # Draw a simple face-like shape
    cv2.ellipse(img, (320, 240), (150, 200), 0, 0, 360, (200, 200, 200), -1)
    cv2.circle(img, (250, 200), 20, (0, 0, 0), -1)
    cv2.circle(img, (390, 200), 20, (0, 0, 0), -1)
    cv2.line(img, (320, 220), (320, 280), (0, 0, 0), 2)
    cv2.ellipse(img, (320, 300), (50, 30), 0, 0, 180, (0, 0, 0), 2)
    return img

@pytest.fixture
def test_image_file(test_data_dir, test_image):
    """Save test image to file."""
    output_path = test_data_dir / "test_face.jpg"
    cv2.imwrite(str(output_path), test_image)
    return output_path

@pytest.fixture
def test_person():
    """Create a test person."""
    return MagicMock(
        id=1,
        name="Test Person",
        face_encodings=[]
    )

@pytest.fixture
def test_face_encoding():
    """Create a test face encoding."""
    return MagicMock(
        id=1,
        person_id=1,
        encoding=np.zeros(128, dtype=np.float64)
    )

@pytest_asyncio.fixture
async def db_session():
    """Create a test database session."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session

@pytest_asyncio.fixture
async def auth_headers():
    """Create authentication headers."""
    return {"Authorization": "Bearer test_token"}

@pytest_asyncio.fixture
async def client():
    """Create a test client."""
    from src.main import app
    from httpx import AsyncClient
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client 