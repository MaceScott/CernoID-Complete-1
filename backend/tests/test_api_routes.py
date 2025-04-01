import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from typing import Generator
import json
from datetime import datetime, timedelta

from app.main import app
from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User
from app.models.person import Person
from app.schemas.person import PersonCreate
from app.tests.fixtures.test_data import test_user, test_person

client = TestClient(app)

@pytest.fixture
def test_token(test_user: User) -> str:
    """Create a test access token"""
    return create_access_token(subject=test_user.id)

@pytest.fixture
def auth_headers(test_token: str) -> dict:
    """Create authorization headers"""
    return {"Authorization": f"Bearer {test_token}"}

class TestAuthRoutes:
    """Test authentication related routes"""
    
    def test_login_success(self, test_user: User):
        """Test successful login"""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "wrong@email.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
    
    def test_get_current_user(self, auth_headers: dict, test_user: User):
        """Test getting current user information"""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email

class TestPersonRoutes:
    """Test person management routes"""
    
    def test_create_person(self, auth_headers: dict, test_person: Person):
        """Test creating a new person"""
        person_data = {
            "name": "Test Person",
            "email": "test@example.com",
            "phone": "1234567890",
            "department": "IT",
            "position": "Developer"
        }
        response = client.post(
            "/api/v1/persons/",
            headers=auth_headers,
            json=person_data
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == person_data["name"]
        assert data["email"] == person_data["email"]
    
    def test_get_persons(self, auth_headers: dict, test_person: Person):
        """Test getting all persons"""
        response = client.get("/api/v1/persons/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_person_by_id(self, auth_headers: dict, test_person: Person):
        """Test getting a specific person by ID"""
        response = client.get(f"/api/v1/persons/{test_person.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_person.id
    
    def test_update_person(self, auth_headers: dict, test_person: Person):
        """Test updating a person"""
        update_data = {
            "name": "Updated Name",
            "email": "updated@example.com"
        }
        response = client.put(
            f"/api/v1/persons/{test_person.id}",
            headers=auth_headers,
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["email"] == update_data["email"]
    
    def test_delete_person(self, auth_headers: dict, test_person: Person):
        """Test deleting a person"""
        response = client.delete(
            f"/api/v1/persons/{test_person.id}",
            headers=auth_headers
        )
        assert response.status_code == 204
        
        # Verify person is deleted
        response = client.get(f"/api/v1/persons/{test_person.id}", headers=auth_headers)
        assert response.status_code == 404

class TestRecognitionRoutes:
    """Test face recognition related routes"""
    
    def test_verify_face(self, auth_headers: dict, test_person: Person):
        """Test face verification endpoint"""
        # Create a test image file
        with open("app/tests/data/test_face.jpg", "rb") as f:
            files = {"file": ("test_face.jpg", f, "image/jpeg")}
            response = client.post(
                f"/api/v1/recognition/verify/{test_person.id}",
                headers=auth_headers,
                files=files
            )
            assert response.status_code == 200
            data = response.json()
            assert "match" in data
            assert "confidence" in data
    
    def test_identify_face(self, auth_headers: dict):
        """Test face identification endpoint"""
        with open("app/tests/data/test_face.jpg", "rb") as f:
            files = {"file": ("test_face.jpg", f, "image/jpeg")}
            response = client.post(
                "/api/v1/recognition/identify",
                headers=auth_headers,
                files=files
            )
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            if data:
                assert "person_id" in data[0]
                assert "confidence" in data[0]
    
    def test_register_face(self, auth_headers: dict, test_person: Person):
        """Test face registration endpoint"""
        with open("app/tests/data/test_face.jpg", "rb") as f:
            files = {"file": ("test_face.jpg", f, "image/jpeg")}
            response = client.post(
                f"/api/v1/recognition/register/{test_person.id}",
                headers=auth_headers,
                files=files
            )
            assert response.status_code == 200
            data = response.json()
            assert "success" in data
            assert data["success"] is True

class TestSystemRoutes:
    """Test system health and monitoring routes"""
    
    def test_health_check(self):
        """Test system health check endpoint"""
        response = client.get("/api/v1/system/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_system_info(self, auth_headers: dict):
        """Test system information endpoint"""
        response = client.get("/api/v1/system/info", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "uptime" in data
        assert "memory_usage" in data
    
    def test_metrics(self, auth_headers: dict):
        """Test metrics endpoint"""
        response = client.get("/api/v1/system/metrics", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "cpu_usage" in data
        assert "memory_usage" in data
        assert "disk_usage" in data

class TestSecurityRoutes:
    """Test security related routes"""
    
    def test_change_password(self, auth_headers: dict):
        """Test password change endpoint"""
        password_data = {
            "current_password": "testpassword123",
            "new_password": "newpassword123"
        }
        response = client.post(
            "/api/v1/security/change-password",
            headers=auth_headers,
            json=password_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Password updated successfully"
    
    def test_reset_password_request(self):
        """Test password reset request endpoint"""
        response = client.post(
            "/api/v1/security/reset-password-request",
            json={"email": "test@example.com"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_reset_password(self):
        """Test password reset endpoint"""
        reset_data = {
            "token": "test_reset_token",
            "new_password": "newpassword123"
        }
        response = client.post(
            "/api/v1/security/reset-password",
            json=reset_data
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_token(self):
        """Test request with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401
    
    def test_expired_token(self):
        """Test request with expired token"""
        expired_token = create_access_token(
            subject=1,
            expires_delta=timedelta(seconds=-1)
        )
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401
    
    def test_invalid_person_id(self, auth_headers: dict):
        """Test request with invalid person ID"""
        response = client.get("/api/v1/persons/999999", headers=auth_headers)
        assert response.status_code == 404
    
    def test_invalid_file_upload(self, auth_headers: dict):
        """Test upload with invalid file type"""
        files = {"file": ("test.txt", b"test content", "text/plain")}
        response = client.post(
            "/api/v1/recognition/identify",
            headers=auth_headers,
            files=files
        )
        assert response.status_code == 400 