"""Tests for security functionality."""
import pytest
from datetime import datetime
from core.database.models import User
from core.security.password import hash_password, verify_password

def test_password_hashing():
    """Test password hashing and verification."""
    password = "testpassword123"
    hashed = hash_password(password)
    
    # Test that hashing produces different results
    assert hashed != password
    assert hash_password(password) != hashed  # Should generate different salt
    
    # Test verification
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_user_password_management(db_session):
    """Test user password management."""
    # Create user with hashed password
    password = "testpassword123"
    user = User(
        username="securityuser",
        email="security@example.com",
        hashed_password=hash_password(password),
        is_active=True,
        is_superuser=False
    )
    db_session.add(user)
    db_session.commit()
    
    # Verify password
    assert verify_password(password, user.hashed_password) is True
    assert verify_password("wrongpassword", user.hashed_password) is False
    
    # Update password
    new_password = "newpassword123"
    user.hashed_password = hash_password(new_password)
    db_session.commit()
    
    # Verify new password
    assert verify_password(new_password, user.hashed_password) is True
    assert verify_password(password, user.hashed_password) is False
    
    # Clean up
    db_session.delete(user)
    db_session.commit()

def test_user_active_status(db_session):
    """Test user active status management."""
    user = User(
        username="statususer",
        email="status@example.com",
        hashed_password=hash_password("testpass123"),
        is_active=True,
        is_superuser=False
    )
    db_session.add(user)
    db_session.commit()
    
    # Test active status
    assert user.is_active is True
    
    # Deactivate user
    user.is_active = False
    db_session.commit()
    
    # Verify deactivation
    updated_user = db_session.query(User).filter_by(id=user.id).first()
    assert updated_user.is_active is False
    
    # Clean up
    db_session.delete(user)
    db_session.commit()

def test_superuser_management(db_session):
    """Test superuser flag management."""
    user = User(
        username="adminuser",
        email="admin@example.com",
        hashed_password=hash_password("adminpass123"),
        is_active=True,
        is_superuser=True
    )
    db_session.add(user)
    db_session.commit()
    
    # Test superuser status
    assert user.is_superuser is True
    
    # Remove superuser status
    user.is_superuser = False
    db_session.commit()
    
    # Verify status change
    updated_user = db_session.query(User).filter_by(id=user.id).first()
    assert updated_user.is_superuser is False
    
    # Clean up
    db_session.delete(user)
    db_session.commit() 