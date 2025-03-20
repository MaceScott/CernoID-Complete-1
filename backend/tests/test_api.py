"""Tests for API endpoints."""
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.core.security import create_access_token
from src.core.database.models.models import User

@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)

@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashedpassword123"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def token(test_user):
    """Create a test token."""
    return create_access_token({"sub": test_user.username})

def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_register_user(client, db_session):
    """Test user registration."""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "strongpassword123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "new@example.com"
    assert "id" in data
    assert "password" not in data

def test_login_user(client, test_user):
    """Test user login."""
    response = client.post(
        "/api/auth/login",
        data={
            "username": test_user.username,
            "password": "hashedpassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_get_current_user(client, token, test_user):
    """Test getting current user details."""
    response = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == test_user.username
    assert data["email"] == test_user.email

def test_update_user(client, token, test_user):
    """Test updating user details."""
    response = client.put(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "email": "updated@example.com"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "updated@example.com"

def test_unauthorized_access(client):
    """Test unauthorized access to protected endpoints."""
    response = client.get("/api/users/me")
    assert response.status_code == 401

def test_invalid_token(client):
    """Test access with invalid token."""
    response = client.get(
        "/api/users/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401

def test_face_recognition_endpoint(client, token, test_user):
    """Test face recognition endpoint."""
    # Create a mock image file
    files = {
        "image": ("test.jpg", b"mock_image_data", "image/jpeg")
    }
    response = client.post(
        "/api/auth/face-login",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code in [200, 401]  # Either successful or unauthorized

def test_access_log_creation(client, token, test_user, db_session):
    """Test access log creation."""
    # Perform an action that should create a log
    client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Check if log was created
    from src.core.database.models.models import AccessLog
    log = db_session.query(AccessLog).filter_by(user_id=test_user.id).first()
    assert log is not None
    assert log.action == "user_access"
    assert log.status == "success" 