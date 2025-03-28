"""Tests for authentication functionality."""
import pytest
import pytest_asyncio
from httpx import AsyncClient
import base64
import cv2
import numpy as np
from pathlib import Path
from src.core.auth import get_password_hash, AuthService
from src.main import app
from src.core.database.models import User
from src.core.security import create_access_token, verify_token
from src.core.config.settings import get_settings

pytestmark = pytest.mark.asyncio

@pytest_asyncio.fixture
async def client():
    """Create a test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture
async def test_user(db_session):
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123")
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
def auth_headers(test_user):
    """Create authentication headers."""
    token = create_access_token({"sub": test_user.username})
    return {"Authorization": f"Bearer {token}"}

async def test_health_check(client: AsyncClient):
    """Test the health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

async def test_login_with_credentials(client: AsyncClient, test_user):
    """Test login with username and password."""
    response = await client.post(
        "/api/v1/auth/token",
        data={
            "username": test_user.username,
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"

async def test_login_with_invalid_credentials(client: AsyncClient):
    """Test login with invalid credentials."""
    response = await client.post(
        "/api/v1/auth/token",
        data={
            "username": "invalid",
            "password": "invalid"
        }
    )
    assert response.status_code == 401
    assert "detail" in response.json()

async def test_register_user(client: AsyncClient):
    """Test user registration."""
    user_data = {
        "username": "newuser",
        "email": "new@example.com",
        "password": "newpassword",
        "full_name": "New User"
    }
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "password" not in data

async def test_register_duplicate_user(client: AsyncClient, test_user):
    """Test registration with duplicate username."""
    user_data = {
        "username": test_user.username,
        "email": "another@example.com",
        "password": "password",
        "full_name": "Another User"
    }
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 400
    assert "detail" in response.json()

async def test_get_current_user(client: AsyncClient, auth_headers, test_user):
    """Test getting current user information."""
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == test_user.username
    assert data["email"] == test_user.email

async def test_get_current_user_invalid_token(client: AsyncClient):
    """Test getting user info with invalid token."""
    headers = {"Authorization": "Bearer invalid_token"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401
    assert "detail" in response.json()

async def test_face_login(client: AsyncClient, test_user):
    """Test login with face recognition."""
    # Create a dummy image for testing
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    _, img_encoded = cv2.imencode('.jpg', img)
    img_base64 = base64.b64encode(img_encoded.tobytes()).decode('utf-8')
    
    response = await client.post(
        "/auth/face-login",
        json={"image": img_base64}
    )
    # Note: This test might fail as it requires face recognition setup
    # We're just testing the endpoint structure
    assert response.status_code in [200, 401]
    if response.status_code == 200:
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer" 