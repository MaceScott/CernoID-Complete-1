import pytest
import pytest_asyncio
from httpx import AsyncClient
from datetime import datetime, timedelta
from src.core.config.settings import get_settings
from src.main import app
from src.core.security import create_access_token

pytestmark = pytest.mark.asyncio

@pytest_asyncio.fixture(autouse=True)
async def setup_system():
    """Setup system monitoring for tests."""
    settings = get_settings()
    # Store original settings
    original_enabled = settings.ENABLE_SYSTEM_MONITORING
    # Disable system monitoring in test environment
    settings.ENABLE_SYSTEM_MONITORING = False
    yield
    # Restore settings after tests
    settings.ENABLE_SYSTEM_MONITORING = original_enabled

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

async def test_system_metrics(client: AsyncClient, admin_headers):
    """Test getting system metrics."""
    response = await client.get("/api/v1/system/metrics", headers=admin_headers)
    # In test environment, system monitoring is disabled
    assert response.status_code == 503
    data = response.json()
    assert "detail" in data
    assert "System monitoring is not available" in data["detail"]

async def test_system_metrics_unauthorized(client: AsyncClient, auth_headers):
    """Test getting system metrics without admin privileges."""
    response = await client.get("/api/v1/system/metrics", headers=auth_headers)
    assert response.status_code == 403

async def test_storage_metrics(client: AsyncClient, admin_headers):
    """Test getting storage metrics."""
    response = await client.get("/api/v1/system/storage", headers=admin_headers)
    # In test environment, system monitoring is disabled
    assert response.status_code == 503
    data = response.json()
    assert "detail" in data
    assert "System monitoring is not available" in data["detail"]

async def test_backup_config(client: AsyncClient, admin_headers):
    """Test getting backup configuration."""
    response = await client.get("/api/v1/system/backup-config", headers=admin_headers)
    # In test environment, system monitoring is disabled
    assert response.status_code == 503
    data = response.json()
    assert "detail" in data
    assert "System monitoring is not available" in data["detail"]

async def test_create_backup(client: AsyncClient, admin_headers):
    """Test creating a system backup."""
    response = await client.post("/api/v1/system/backup", headers=admin_headers)
    # In test environment, system monitoring is disabled
    assert response.status_code == 503
    data = response.json()
    assert "detail" in data
    assert "System monitoring is not available" in data["detail"]

async def test_admin_stats(client: AsyncClient, admin_headers):
    """Test getting admin statistics."""
    response = await client.get("/api/v1/system/admin/stats", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_users" in data
    assert "active_users" in data
    assert "total_recognitions" in data
    assert "successful_recognitions" in data

async def test_admin_access_logs(client: AsyncClient, admin_headers):
    """Test getting admin access logs."""
    response = await client.get("/api/v1/system/admin/logs", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for log in data:
        assert "timestamp" in log
        assert "user_id" in log
        assert "action" in log
        assert "status" in log

async def test_admin_users(client: AsyncClient, admin_headers):
    """Test getting admin user list."""
    response = await client.get("/api/v1/system/admin/users", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for user in data:
        assert "id" in user
        assert "username" in user
        assert "email" in user
        assert "is_active" in user
        assert "is_superuser" in user

async def test_system_health(client: AsyncClient):
    """Test system health check."""
    response = await client.get("/api/v1/system/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "database" in data
    assert "face_recognition" in data
    assert "storage" in data 