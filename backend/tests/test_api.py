"""Tests for API endpoints."""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from src.main import app
from src.core.security import create_access_token
from src.core.database.models import User, FaceEncoding, AccessLog, Person, Camera, Recognition
from src.core.config.settings import get_settings
from src.core.database.base import get_session_context

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
        hashed_password="hashedpassword123"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
def token(test_user):
    """Create a test token."""
    return create_access_token({"sub": test_user.username})

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
async def test_create_person(client, token):
    """Test creating a person."""
    response = await client.post(
        "/api/persons",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Test Person",
            "email": "person@example.com",
            "phone": "1234567890"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Person"
    assert data["email"] == "person@example.com"
    assert data["phone"] == "1234567890"

@pytest.mark.asyncio
async def test_get_persons(client, token):
    """Test getting all persons."""
    response = await client.get(
        "/api/persons",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_get_person(client, token):
    """Test getting a specific person."""
    # First create a person
    create_response = await client.post(
        "/api/persons",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Test Person",
            "email": "person@example.com",
            "phone": "1234567890"
        }
    )
    person_id = create_response.json()["id"]

    # Then get the person
    response = await client.get(
        f"/api/persons/{person_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Person"
    assert data["email"] == "person@example.com"
    assert data["phone"] == "1234567890"

@pytest.mark.asyncio
async def test_update_person(client, token):
    """Test updating a person."""
    # First create a person
    create_response = await client.post(
        "/api/persons",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Test Person",
            "email": "person@example.com",
            "phone": "1234567890"
        }
    )
    person_id = create_response.json()["id"]

    # Then update the person
    response = await client.put(
        f"/api/persons/{person_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Updated Person",
            "email": "updated@example.com",
            "phone": "0987654321"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Person"
    assert data["email"] == "updated@example.com"
    assert data["phone"] == "0987654321"

@pytest.mark.asyncio
async def test_delete_person(client, token):
    """Test deleting a person."""
    # First create a person
    create_response = await client.post(
        "/api/persons",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Test Person",
            "email": "person@example.com",
            "phone": "1234567890"
        }
    )
    person_id = create_response.json()["id"]

    # Then delete the person
    response = await client.delete(
        f"/api/persons/{person_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    # Verify the person is deleted
    get_response = await client.get(
        f"/api/persons/{person_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_response.status_code == 404 