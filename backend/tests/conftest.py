"""Test configuration and fixtures."""
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
from typing import Generator, Dict, Any, List, Optional, Tuple, AsyncGenerator
from dotenv import load_dotenv
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import numpy as np
import cv2
import concurrent.futures
import asyncio
from datetime import datetime, timedelta

# Set test environment and load test environment variables
os.environ["TESTING"] = "true"
load_dotenv(Path(__file__).parent.parent / '.env.test', override=True)

# Add backend and backend/src to Python path
backend_dir = str(Path(__file__).parent.parent)
backend_src = str(Path(__file__).parent.parent / "src")
sys.path.insert(0, backend_dir)
sys.path.insert(0, backend_src)

# Import application components
from src.main import create_app
from src.core.config.settings import get_settings
from src.core.database import get_db, init_db
from src.core.database.models import Base, User, Camera, Recognition, Person, FaceEncoding, AccessLog
from src.core.auth import AuthService, get_auth_service
from src.core.recognition import FaceRecognitionSystem, get_recognition_system
from src.core.recognition.matcher import FaceMatcher
from src.core.video import VideoProcessor
from src.core.monitoring import MonitoringService
from src.core.events import EventManager

# Mock redis before any imports
mock_redis = AsyncMock()
mock_redis.Redis = AsyncMock()
mock_redis.Redis.from_url = AsyncMock(return_value=AsyncMock())
mock_redis.Redis.pipeline = AsyncMock(return_value=AsyncMock())
mock_redis.Redis.get = AsyncMock(return_value=None)
mock_redis.Redis.set = AsyncMock(return_value=True)
mock_redis.Redis.delete = AsyncMock(return_value=True)
mock_redis.Redis.exists = AsyncMock(return_value=False)
mock_redis.Redis.keys = AsyncMock(return_value=[])
mock_redis.Redis.hget = AsyncMock(return_value=None)
mock_redis.Redis.hset = AsyncMock(return_value=True)
mock_redis.Redis.hdel = AsyncMock(return_value=True)
mock_redis.Redis.hexists = AsyncMock(return_value=False)
mock_redis.Redis.hkeys = AsyncMock(return_value=[])
mock_redis.Redis.hgetall = AsyncMock(return_value={})

# Mock plotly before any imports
mock_plotly = MagicMock()
mock_plotly.graph_objects = MagicMock()
mock_plotly.express = MagicMock()
mock_plotly.subplots = MagicMock()

# Mock scipy before any imports
mock_scipy = MagicMock()
mock_scipy.spatial = MagicMock()
mock_scipy.spatial.distance = MagicMock()

# Mock pandas before any imports
mock_pandas = MagicMock()
mock_pandas.DataFrame = MagicMock()
mock_pandas.Series = MagicMock()

# Mock numpy before any imports
mock_numpy = MagicMock()
mock_numpy.array = np.array
mock_numpy.zeros = np.zeros
mock_numpy.ones = np.ones
mock_numpy.random = np.random

# Mock OpenCV before any imports
mock_cv2 = MagicMock()
mock_cv2.imread = cv2.imread
mock_cv2.imwrite = cv2.imwrite
mock_cv2.resize = cv2.resize
mock_cv2.cvtColor = cv2.cvtColor
mock_cv2.COLOR_BGR2RGB = cv2.COLOR_BGR2RGB
mock_cv2.COLOR_RGB2BGR = cv2.COLOR_RGB2BGR

# Apply mocks
sys.modules['redis'] = mock_redis
sys.modules['plotly'] = mock_plotly
sys.modules['plotly.graph_objects'] = mock_plotly.graph_objects
sys.modules['plotly.express'] = mock_plotly.express
sys.modules['plotly.subplots'] = mock_plotly.subplots
sys.modules['scipy'] = mock_scipy
sys.modules['scipy.spatial'] = mock_scipy.spatial
sys.modules['scipy.spatial.distance'] = mock_scipy.spatial.distance
sys.modules['pandas'] = mock_pandas
sys.modules['numpy'] = mock_numpy
sys.modules['cv2'] = mock_cv2

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def engine():
    """Create a test database engine."""
    settings = get_settings()
    test_engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True,
        poolclass=NullPool
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield test_engine
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()

@pytest_asyncio.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()

# Now import the application modules
import pytest
from src.main import create_app

# Set testing environment
os.environ["TESTING"] = "1"

# Mock environment variables before importing settings
os.environ["MODEL_PATH"] = "test_models"
os.environ["GPU_DEVICE"] = "cuda:0"
os.environ["FACE_RECOGNITION_MODEL"] = "test_face_model"
os.environ["FACE_DETECTION_MODEL"] = "test_detection_model"

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_env():
    """Set up test environment."""
    # Mock face recognition system
    mock_face_recognition = MockFaceRecognitionSystem()
    await mock_face_recognition.initialize()
    
    with patch("core.face_recognition.core.FaceRecognitionSystem", return_value=mock_face_recognition):
        yield

@pytest.fixture(scope="session")
def mock_gpu():
    """Mock GPU utilities."""
    return mock_gputil

@pytest_asyncio.fixture(scope="session")
async def mock_face_detector():
    """Mock face detector."""
    detector = AsyncMock()
    detector.detect_faces = AsyncMock(return_value=[(0, 0, 100, 100)])
    return detector

@pytest_asyncio.fixture(scope="session")
async def mock_face_recognizer():
    """Mock face recognizer."""
    recognizer = AsyncMock()
    recognizer.get_encoding = AsyncMock(return_value=[0.0] * 128)
    return recognizer

@pytest_asyncio.fixture(scope="session")
async def mock_face_matcher():
    """Mock face matcher."""
    return MockFaceMatcher()

@pytest.fixture(scope="session")
def test_settings():
    """Test settings."""
    from src.core.config import Settings
    settings = Settings()
    settings.SECRET_KEY = "test-secret-key"
    settings.ALGORITHM = "HS256"
    settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
    settings.REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
    return settings

@pytest.fixture
async def app(db_session):
    """Create a test FastAPI application."""
    from fastapi import FastAPI
    from src.core.database.session import DatabaseSession, db_session
    
    # Initialize the database session
    await db_session.initialize()
    
    # Create FastAPI app
    app = FastAPI()
    
    # Initialize database tables
    await init_db()
    
    yield app
    
    # Cleanup
    await db_session.cleanup()

@pytest_asyncio.fixture(scope="session")
async def client(app):
    """Create test client."""
    from fastapi.testclient import TestClient
    
    async with TestClient(app) as test_client:
        yield test_client

@pytest.fixture(scope="session")
def test_image() -> bytes:
    """Create test image."""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    _, img_bytes = cv2.imencode('.jpg', img)
    return img_bytes.tobytes()

@pytest.fixture(scope="session")
def test_image_file(tmp_path_factory, test_image) -> Path:
    """Create test image file."""
    img_path = tmp_path_factory.mktemp("data") / "test.jpg"
    img_path.write_bytes(test_image)
    return img_path

@pytest_asyncio.fixture
async def auth_service() -> AuthService:
    """Get a test auth service."""
    return AuthService(settings)

@pytest_asyncio.fixture
async def face_recognition_system() -> FaceRecognitionSystem:
    """Get a test face recognition system."""
    return FaceRecognitionSystem()

@pytest_asyncio.fixture
async def face_matcher() -> FaceMatcher:
    """Get a test face matcher."""
    return FaceMatcher({})

@pytest_asyncio.fixture
async def video_processor() -> VideoProcessor:
    """Get a test video processor."""
    return VideoProcessor({})

@pytest_asyncio.fixture
async def monitoring_service() -> MonitoringService:
    """Get a test monitoring service."""
    return MonitoringService()

@pytest_asyncio.fixture
async def event_manager() -> EventManager:
    """Get a test event manager."""
    return EventManager()

@pytest_asyncio.fixture
async def test_user(db: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="test_user",
        hashed_password="test_password",
        role="user"
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@pytest_asyncio.fixture
async def test_admin(db: AsyncSession) -> User:
    """Create a test admin user."""
    admin = User(
        email="admin@example.com",
        username="test_admin",
        hashed_password="admin_password",
        role="admin"
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return admin

@pytest_asyncio.fixture
async def test_camera(db: AsyncSession) -> Camera:
    """Create a test camera."""
    camera = Camera(
        name="Test Camera",
        url="rtsp://test.camera",
        location="Test Location",
        status="active"
    )
    db.add(camera)
    await db.commit()
    await db.refresh(camera)
    return camera

@pytest_asyncio.fixture
async def test_person(db: AsyncSession) -> Person:
    """Create a test person."""
    person = Person(
        name="Test Person",
        email="person@example.com",
        phone="1234567890",
        status="active"
    )
    db.add(person)
    await db.commit()
    await db.refresh(person)
    return person

@pytest_asyncio.fixture
async def test_face_encoding(db: AsyncSession, test_person: Person) -> FaceEncoding:
    """Create a test face encoding."""
    encoding = FaceEncoding(
        person_id=test_person.id,
        encoding=np.random.rand(128).tobytes(),
        quality=0.8,
        metadata={"source": "test"}
    )
    db.add(encoding)
    await db.commit()
    await db.refresh(encoding)
    return encoding

@pytest_asyncio.fixture
async def test_recognition(db: AsyncSession, test_person: Person, test_camera: Camera) -> Recognition:
    """Create a test recognition."""
    recognition = Recognition(
        person_id=test_person.id,
        camera_id=test_camera.id,
        confidence=0.9,
        timestamp=datetime.utcnow(),
        metadata={"source": "test"}
    )
    db.add(recognition)
    await db.commit()
    await db.refresh(recognition)
    return recognition

@pytest_asyncio.fixture
async def test_access_log(db: AsyncSession, test_person: Person, test_camera: Camera) -> AccessLog:
    """Create a test access log."""
    access_log = AccessLog(
        person_id=test_person.id,
        camera_id=test_camera.id,
        access_type="entry",
        timestamp=datetime.utcnow(),
        metadata={"source": "test"}
    )
    db.add(access_log)
    await db.commit()
    await db.refresh(access_log)
    return access_log 