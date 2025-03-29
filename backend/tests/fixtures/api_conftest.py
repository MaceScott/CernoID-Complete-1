"""API test configuration."""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
import asyncio
from src.core.security import create_access_token
from src.core.database.models import User

@pytest_asyncio.fixture
async def event_loop():
    """Create an event loop for the test."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture
async def app():
    """Create a test FastAPI app."""
    from src.main import create_app
    app = create_app()
    return app

@pytest_asyncio.fixture
async def client(app):
    """Create a test client."""
    from httpx import AsyncClient
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture
async def test_image():
    """Create a test image."""
    return MagicMock()

@pytest_asyncio.fixture
async def test_image_file():
    """Create a test image file."""
    return MagicMock()

@pytest_asyncio.fixture
async def monitoring_service():
    """Create a mock monitoring service."""
    return AsyncMock()

@pytest_asyncio.fixture
async def event_manager():
    """Create a mock event manager."""
    return AsyncMock()

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