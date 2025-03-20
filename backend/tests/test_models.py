"""Tests for database models."""
import pytest
from datetime import datetime
from core.database.models import User, FaceEncoding, AccessLog

def test_create_user(db_session):
    """Test user creation."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashedpassword123"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.hashed_password == "hashedpassword123"
    assert user.is_active is True
    assert user.is_superuser is False
    assert isinstance(user.created_at, datetime)
    assert isinstance(user.updated_at, datetime)

def test_create_face_encoding(db_session):
    """Test face encoding creation."""
    # Create a user first
    user = User(
        username="faceuser",
        email="face@example.com",
        hashed_password="hashedpassword123"
    )
    db_session.add(user)
    db_session.commit()

    # Create face encoding
    encoding = FaceEncoding(
        user_id=user.id,
        encoding_data=b"test_encoding_data"
    )
    db_session.add(encoding)
    db_session.commit()
    db_session.refresh(encoding)

    assert encoding.id is not None
    assert encoding.user_id == user.id
    assert encoding.encoding_data == b"test_encoding_data"
    assert isinstance(encoding.created_at, datetime)
    assert isinstance(encoding.updated_at, datetime)

def test_create_access_log(db_session):
    """Test access log creation."""
    # Create a user first
    user = User(
        username="loguser",
        email="log@example.com",
        hashed_password="hashedpassword123"
    )
    db_session.add(user)
    db_session.commit()

    # Create access log
    log = AccessLog(
        user_id=user.id,
        action="login",
        status="success",
        details={"ip": "127.0.0.1"}
    )
    db_session.add(log)
    db_session.commit()
    db_session.refresh(log)

    assert log.id is not None
    assert log.user_id == user.id
    assert log.action == "login"
    assert log.status == "success"
    assert log.details == {"ip": "127.0.0.1"}
    assert isinstance(log.timestamp, datetime)

def test_cascade_delete_user(db_session):
    """Test that deleting a user cascades to related records."""
    # Create user
    user = User(
        username="cascadeuser",
        email="cascade@example.com",
        hashed_password="hashedpassword123"
    )
    db_session.add(user)
    db_session.commit()

    # Create face encoding
    encoding = FaceEncoding(
        user_id=user.id,
        encoding_data=b"test_encoding_data"
    )
    db_session.add(encoding)

    # Create access log
    log = AccessLog(
        user_id=user.id,
        action="test",
        status="success"
    )
    db_session.add(log)
    db_session.commit()

    # Delete user
    db_session.delete(user)
    db_session.commit()

    # Verify cascade
    assert db_session.query(FaceEncoding).filter_by(user_id=user.id).first() is None
    assert db_session.query(AccessLog).filter_by(user_id=user.id).first() is None

def test_unique_constraints(db_session):
    """Test unique constraints on username and email."""
    # Create first user
    user1 = User(
        username="uniqueuser",
        email="unique@example.com",
        hashed_password="hashedpassword123"
    )
    db_session.add(user1)
    db_session.commit()

    # Try to create user with same username
    with pytest.raises(Exception):
        user2 = User(
            username="uniqueuser",
            email="different@example.com",
            hashed_password="hashedpassword123"
        )
        db_session.add(user2)
        db_session.commit()

    # Try to create user with same email
    with pytest.raises(Exception):
        user3 = User(
            username="differentuser",
            email="unique@example.com",
            hashed_password="hashedpassword123"
        )
        db_session.add(user3)
        db_session.commit() 