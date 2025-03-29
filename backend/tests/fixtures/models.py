"""Model test fixtures."""
import pytest
from src.core.database.models import Camera, Person, FaceEncoding, Recognition, AccessLog

@pytest.fixture
def test_camera():
    """Create a test camera."""
    return Camera(
        name="Test Camera",
        location="Test Location",
        ip_address="192.168.1.1",
        port=8080
    )

@pytest.fixture
def test_person():
    """Create a test person."""
    return Person(
        name="Test Person",
        email="person@example.com",
        phone="1234567890"
    )

@pytest.fixture
def test_face_encoding():
    """Create a test face encoding."""
    return FaceEncoding(
        encoding_data=[0.0] * 128,
        person_id=1
    )

@pytest.fixture
def test_recognition():
    """Create a test recognition."""
    return Recognition(
        person_id=1,
        camera_id=1,
        confidence=0.95,
        timestamp="2024-03-29T00:00:00"
    )

@pytest.fixture
def test_access_log():
    """Create a test access log."""
    return AccessLog(
        person_id=1,
        camera_id=1,
        timestamp="2024-03-29T00:00:00",
        access_type="entry"
    ) 