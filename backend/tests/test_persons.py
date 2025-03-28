"""Tests for person management functionality."""
import pytest
import pytest_asyncio
from httpx import AsyncClient
import base64
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
from src.core.database.models import Person, FaceEncoding
from src.main import app
from src.core.security import create_access_token

pytestmark = pytest.mark.asyncio

@pytest_asyncio.fixture
async def test_person(db_session):
    """Create a test person."""
    person = Person(
        full_name="Test Person",
        email="person@example.com",
        phone="+1234567890",
        department="IT",
        position="Developer",
        active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(person)
    await db_session.commit()
    await db_session.refresh(person)
    yield person
    await db_session.delete(person)
    await db_session.commit()

@pytest_asyncio.fixture
async def client():
    """Create a test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

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

async def test_create_person(client: AsyncClient, admin_headers):
    """Test person creation."""
    person_data = {
        "full_name": "New Person",
        "email": "new@example.com",
        "phone": "+1234567890",
        "department": "HR",
        "position": "Manager",
        "active": True
    }
    response = await client.post("/api/v1/persons/", json=person_data, headers=admin_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["full_name"] == person_data["full_name"]
    assert data["email"] == person_data["email"]
    assert data["phone"] == person_data["phone"]
    assert data["department"] == person_data["department"]
    assert data["position"] == person_data["position"]
    assert data["active"] == person_data["active"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data

async def test_create_person_unauthorized(client: AsyncClient, auth_headers):
    """Test creating a person without admin privileges."""
    person_data = {
        "full_name": "New Person",
        "email": "new.person@example.com",
        "phone": "+1234567890"
    }
    response = await client.post("/api/persons/", json=person_data, headers=auth_headers)
    assert response.status_code == 403
    assert "detail" in response.json()

async def test_get_person(client: AsyncClient, auth_headers, test_person):
    """Test getting a person by ID."""
    response = await client.get(f"/api/persons/{test_person.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_person.id
    assert data["full_name"] == test_person.full_name
    assert data["email"] == test_person.email
    assert data["phone"] == test_person.phone

async def test_get_nonexistent_person(client: AsyncClient, auth_headers):
    """Test getting a nonexistent person."""
    response = await client.get("/api/persons/999", headers=auth_headers)
    assert response.status_code == 404
    assert "detail" in response.json()

async def test_update_person(client: AsyncClient, admin_headers, test_person):
    """Test updating a person."""
    update_data = {
        "full_name": "Updated Person",
        "email": "updated@example.com",
        "phone": "+9876543210",
        "department": "Finance",
        "position": "Senior Manager",
        "active": False
    }
    response = await client.put(
        f"/api/persons/{test_person.id}",
        json=update_data,
        headers=admin_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == update_data["full_name"]
    assert data["email"] == update_data["email"]
    assert data["phone"] == update_data["phone"]
    assert data["department"] == update_data["department"]
    assert data["position"] == update_data["position"]
    assert data["active"] == update_data["active"]
    assert data["id"] == test_person.id

async def test_update_person_unauthorized(client: AsyncClient, auth_headers, test_person):
    """Test updating a person without admin privileges."""
    update_data = {
        "full_name": "Updated Person",
        "email": "updated@example.com"
    }
    response = await client.put(
        f"/api/persons/{test_person.id}",
        json=update_data,
        headers=auth_headers
    )
    assert response.status_code == 403
    assert "detail" in response.json()

async def test_delete_person(client: AsyncClient, admin_headers, test_person):
    """Test deleting a person."""
    response = await client.delete(
        f"/api/persons/{test_person.id}",
        headers=admin_headers
    )
    assert response.status_code == 200
    
    # Verify the person is deleted
    get_response = await client.get(
        f"/api/persons/{test_person.id}",
        headers=admin_headers
    )
    assert get_response.status_code == 404

async def test_delete_person_unauthorized(client: AsyncClient, auth_headers, test_person):
    """Test deleting a person without admin privileges."""
    response = await client.delete(
        f"/api/persons/{test_person.id}",
        headers=auth_headers
    )
    assert response.status_code == 403
    assert "detail" in response.json()

async def test_list_persons(client: AsyncClient, auth_headers):
    """Test listing all persons."""
    response = await client.get("/api/persons/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

async def test_list_persons_with_filters(client: AsyncClient, auth_headers):
    """Test listing persons with filters."""
    response = await client.get(
        "/api/persons/",
        params={
            "department": "IT",
            "active": "true",
            "skip": 0,
            "limit": 10
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list) 