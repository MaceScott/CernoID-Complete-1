"""Tests for face recognition functionality."""
import pytest
import pytest_asyncio
from httpx import AsyncClient
import base64
import cv2
import numpy as np
from pathlib import Path
from unittest.mock import AsyncMock, patch
from src.core.config.settings import get_settings
from src.core.recognition import FaceRecognitionSystem
from src.main import app
from src.core.security import create_access_token
from src.core.database.models import User, Person, FaceEncoding

pytestmark = pytest.mark.asyncio

@pytest_asyncio.fixture
async def auth_headers():
    """Create authentication headers."""
    token = create_access_token({"sub": "testuser"})
    return {"Authorization": f"Bearer {token}"}

@pytest_asyncio.fixture
async def admin_headers():
    """Create admin authentication headers."""
    token = create_access_token({"sub": "admin", "is_superuser": True})
    return {"Authorization": f"Bearer {token}"}

@pytest_asyncio.fixture(autouse=True)
async def setup_recognition():
    """Setup face recognition for tests."""
    settings = get_settings()
    
    # Store original settings
    original_enabled = settings.ENABLE_FACE_RECOGNITION
    original_gpu = settings.USE_GPU
    original_testing = settings.TESTING
    
    # Disable face recognition in test environment
    settings.ENABLE_FACE_RECOGNITION = False
    settings.USE_GPU = False
    settings.TESTING = True
    
    yield
    
    # Restore original settings
    settings.ENABLE_FACE_RECOGNITION = original_enabled
    settings.USE_GPU = original_gpu
    settings.TESTING = original_testing

@pytest_asyncio.fixture
async def test_person(db_session):
    """Create a test person."""
    person = Person(
        full_name="Test Person",
        email="person@example.com",
        phone="+1234567890",
        department="IT",
        position="Developer",
        active=True
    )
    db_session.add(person)
    await db_session.commit()
    await db_session.refresh(person)
    return person

@pytest_asyncio.fixture
async def test_face_encoding(db_session, test_person):
    """Create a test face encoding."""
    encoding = FaceEncoding(
        person_id=test_person.id,
        encoding_data=np.random.rand(128).tobytes()
    )
    db_session.add(encoding)
    await db_session.commit()
    await db_session.refresh(encoding)
    return encoding

@pytest.fixture
def test_image():
    """Create a test image."""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.rectangle(img, (25, 25), (75, 75), (255, 255, 255), -1)
    return img

@pytest.fixture
def test_image_file(tmp_path):
    """Create a test image file."""
    img = test_image()
    img_path = tmp_path / "test.jpg"
    cv2.imwrite(str(img_path), img)
    return img_path

async def test_recognize_faces(client, auth_headers, test_image):
    """Test face recognition endpoint."""
    _, img_encoded = cv2.imencode('.jpg', test_image)
    img_base64 = base64.b64encode(img_encoded.tobytes()).decode('utf-8')
    
    response = await client.post(
        "/api/recognition/recognize",
        headers=auth_headers,
        json={"image": img_base64}
    )
    assert response.status_code == 200
    data = response.json()
    assert "faces" in data
    assert isinstance(data["faces"], list)

async def test_recognize_faces_unauthorized(client, test_image):
    """Test face recognition without authentication."""
    _, img_encoded = cv2.imencode('.jpg', test_image)
    img_base64 = base64.b64encode(img_encoded.tobytes()).decode('utf-8')
    
    response = await client.post(
        "/api/recognition/recognize",
        json={"image": img_base64}
    )
    assert response.status_code == 401

async def test_recognize_file(client, auth_headers, test_image_file):
    """Test face recognition with file upload."""
    with open(test_image_file, "rb") as f:
        files = {"file": ("test.jpg", f, "image/jpeg")}
        response = await client.post(
            "/api/recognition/recognize-file",
            headers=auth_headers,
            files=files
        )
    assert response.status_code == 200
    data = response.json()
    assert "faces" in data
    assert isinstance(data["faces"], list)

async def test_recognize_invalid_image(client, auth_headers):
    """Test face recognition with invalid image."""
    response = await client.post(
        "/api/recognition/recognize",
        headers=auth_headers,
        json={"image": "invalid_base64"}
    )
    assert response.status_code == 400
    assert "detail" in response.json()

async def test_recognize_with_high_confidence(client, auth_headers, test_image):
    """Test face recognition with high confidence threshold."""
    _, img_encoded = cv2.imencode('.jpg', test_image)
    img_base64 = base64.b64encode(img_encoded.tobytes()).decode('utf-8')
    
    response = await client.post(
        "/api/recognition/recognize",
        headers=auth_headers,
        json={
            "image": img_base64,
            "confidence_threshold": 0.9
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "faces" in data
    assert isinstance(data["faces"], list)

async def test_search_faces(client, auth_headers, test_image):
    """Test face search endpoint."""
    _, img_encoded = cv2.imencode('.jpg', test_image)
    img_base64 = base64.b64encode(img_encoded.tobytes()).decode('utf-8')
    
    response = await client.post(
        "/api/recognition/search",
        headers=auth_headers,
        json={"image": img_base64}
    )
    assert response.status_code == 200
    data = response.json()
    assert "matches" in data
    assert isinstance(data["matches"], list)

async def test_face_detection(client, auth_headers, test_image):
    """Test face detection endpoint."""
    _, img_encoded = cv2.imencode('.jpg', test_image)
    img_base64 = base64.b64encode(img_encoded.tobytes()).decode('utf-8')
    
    response = await client.post(
        "/api/recognition/detect",
        headers=auth_headers,
        json={"image": img_base64}
    )
    assert response.status_code == 200
    data = response.json()
    assert "faces" in data
    assert isinstance(data["faces"], list) 