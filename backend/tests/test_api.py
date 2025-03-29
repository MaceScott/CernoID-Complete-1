"""Tests for API endpoints."""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from src.core.security import create_access_token
from src.core.database.models import User
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@pytest.mark.asyncio
async def test_register_user(client, db_session):
    """Test user registration."""
    response = await client.post(
        "/api/auth/register",
        json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "strongpassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "new@example.com"
    assert "password" not in data

@pytest.mark.asyncio
async def test_login_user(client, test_user):
    """Test user login."""
    response = await client.post(
        "/api/auth/token",
        data={
            "username": test_user.username,
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_get_current_user(client, token):
    """Test getting current user."""
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"

@pytest.mark.asyncio
async def test_get_current_user_invalid_token(client):
    """Test getting current user with invalid token."""
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert "detail" in response.json()

@pytest.mark.asyncio
async def test_api_initialization(app):
    """Test API initialization."""
    assert app is not None

@pytest.mark.asyncio
async def test_client_initialization(client):
    """Test client initialization."""
    assert client is not None 