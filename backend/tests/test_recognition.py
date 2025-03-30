"""Tests for face recognition functionality."""
import pytest
import pytest_asyncio
from httpx import AsyncClient
import base64
import cv2
import numpy as np
from pathlib import Path
from unittest.mock import AsyncMock, patch

# Import mock dlib before any other imports
from tests.fixtures.mock_dlib import mock_dlib

from src.core.config.settings import get_settings
from src.core.face_recognition import FaceRecognitionSystem
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

@pytest.mark.asyncio
async def test_recognize_face(client, auth_headers, test_image_file):
    """Test face recognition endpoint."""
    # Read the test image
    with open(test_image_file, "rb") as f:
        image_data = f.read()
    
    # Encode the image as base64
    image_base64 = base64.b64encode(image_data).decode()
    
    # Make the request
    response = await client.post(
        "/api/v1/recognition/recognize",
        headers=auth_headers,
        json={"image_data": image_base64}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "faces" in data
    assert isinstance(data["faces"], list)

@pytest.mark.asyncio
async def test_unauthorized_access(client):
    """Test unauthorized access to recognition endpoint."""
    response = await client.post(
        "/api/v1/recognition/recognize",
        json={"image_data": "test"}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_invalid_image(client, auth_headers):
    """Test recognition with invalid image data."""
    response = await client.post(
        "/api/v1/recognition/recognize",
        headers=auth_headers,
        json={"image_data": "invalid_base64"}
    )
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_recognize_faces(client, auth_headers, test_image):
    """Test face recognition endpoint."""
    _, img_encoded = cv2.imencode('.jpg', test_image)
    img_base64 = base64.b64encode(img_encoded.tobytes()).decode('utf-8')
    
    response = await client.post(
        "/api/v1/recognition/recognize",
        headers=auth_headers,
        json={"image_data": img_base64}
    )
    assert response.status_code == 200
    data = response.json()
    assert "faces" in data
    assert isinstance(data["faces"], list)

@pytest.mark.asyncio
async def test_recognize_faces_unauthorized(client, test_image):
    """Test face recognition without authentication."""
    _, img_encoded = cv2.imencode('.jpg', test_image)
    img_base64 = base64.b64encode(img_encoded.tobytes()).decode('utf-8')
    
    response = await client.post(
        "/api/v1/recognition/recognize",
        json={"image_data": img_base64}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_recognize_file(client, auth_headers, test_image_file):
    """Test face recognition with file upload."""
    with open(test_image_file, "rb") as f:
        files = {"file": ("test.jpg", f, "image/jpeg")}
        response = await client.post(
            "/api/v1/recognition/recognize",
            headers=auth_headers,
            files=files
        )
    assert response.status_code == 200
    data = response.json()
    assert "faces" in data
    assert isinstance(data["faces"], list)

@pytest.mark.asyncio
async def test_recognize_with_high_confidence(client, auth_headers, test_image):
    """Test face recognition with high confidence threshold."""
    _, img_encoded = cv2.imencode('.jpg', test_image)
    img_base64 = base64.b64encode(img_encoded.tobytes()).decode('utf-8')
    
    response = await client.post(
        "/api/v1/recognition/recognize",
        headers=auth_headers,
        json={
            "image_data": img_base64,
            "min_confidence": 0.9
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "faces" in data
    assert isinstance(data["faces"], list)

@pytest.mark.asyncio
async def test_search_faces(client, auth_headers, test_image):
    """Test face search endpoint."""
    _, img_encoded = cv2.imencode('.jpg', test_image)
    img_base64 = base64.b64encode(img_encoded.tobytes()).decode('utf-8')
    
    response = await client.post(
        "/api/v1/recognition/search",
        headers=auth_headers,
        json={"image_data": img_base64}
    )
    assert response.status_code == 200
    data = response.json()
    assert "matches" in data
    assert isinstance(data["matches"], list)

@pytest.mark.asyncio
async def test_face_detection(client, auth_headers, test_image):
    """Test face detection endpoint."""
    _, img_encoded = cv2.imencode('.jpg', test_image)
    img_base64 = base64.b64encode(img_encoded.tobytes()).decode('utf-8')
    
    response = await client.post(
        "/api/v1/recognition/detect",
        headers=auth_headers,
        json={"image_data": img_base64}
    )
    assert response.status_code == 200
    data = response.json()
    assert "faces" in data
    assert isinstance(data["faces"], list) 