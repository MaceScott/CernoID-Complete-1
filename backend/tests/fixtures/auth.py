"""Authentication test fixtures."""
import pytest
from src.core.config.settings import Settings

@pytest.fixture
def test_settings():
    """Create test settings."""
    return Settings(
        SECRET_KEY="test_secret_key",
        ALGORITHM="HS256",
        ACCESS_TOKEN_EXPIRE_MINUTES=30
    )

@pytest.fixture
def auth_service():
    """Create a mock auth service."""
    from unittest.mock import AsyncMock
    service = AsyncMock()
    service.authenticate = AsyncMock()
    service.create_access_token = AsyncMock()
    return service

@pytest.fixture
def test_admin():
    """Create a test admin user."""
    from src.core.database.models import User
    return User(
        username="admin",
        email="admin@example.com",
        hashed_password="hashedpassword123",
        is_admin=True
    ) 