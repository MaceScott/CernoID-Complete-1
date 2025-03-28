"""Tests for security functionality."""
import pytest
import pytest_asyncio
from datetime import datetime
from src.core.database.models import User
from src.core.security.password import hash_password, verify_password
from src.core.security import create_access_token, verify_token
from src.core.config.settings import get_settings

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

@pytest.mark.asyncio
async def test_user_password_management(db_session):
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
    await db_session.commit()
    
    # Verify password
    assert verify_password(password, user.hashed_password) is True
    assert verify_password("wrongpassword", user.hashed_password) is False
    
    # Update password
    new_password = "newpassword123"
    user.hashed_password = hash_password(new_password)
    await db_session.commit()
    
    # Verify new password
    assert verify_password(new_password, user.hashed_password) is True
    assert verify_password(password, user.hashed_password) is False
    
    # Clean up
    await db_session.delete(user)
    await db_session.commit()

@pytest.mark.asyncio
async def test_user_active_status(db_session):
    """Test user active status management."""
    # Create active user
    user = User(
        username="activeuser",
        email="active@example.com",
        hashed_password=hash_password("testpassword123"),
        is_active=True,
        is_superuser=False
    )
    db_session.add(user)
    await db_session.commit()
    
    # Verify active status
    assert user.is_active is True
    
    # Deactivate user
    user.is_active = False
    await db_session.commit()
    
    # Verify inactive status
    assert user.is_active is False
    
    # Reactivate user
    user.is_active = True
    await db_session.commit()
    
    # Verify active status again
    assert user.is_active is True
    
    # Clean up
    await db_session.delete(user)
    await db_session.commit()

@pytest.mark.asyncio
async def test_superuser_management(db_session):
    """Test superuser management."""
    # Create regular user
    user = User(
        username="regularuser",
        email="regular@example.com",
        hashed_password=hash_password("testpassword123"),
        is_active=True,
        is_superuser=False
    )
    db_session.add(user)
    await db_session.commit()
    
    # Verify regular user status
    assert user.is_superuser is False
    
    # Make user superuser
    user.is_superuser = True
    await db_session.commit()
    
    # Verify superuser status
    assert user.is_superuser is True
    
    # Remove superuser status
    user.is_superuser = False
    await db_session.commit()
    
    # Verify regular user status again
    assert user.is_superuser is False
    
    # Clean up
    await db_session.delete(user)
    await db_session.commit()

def test_token_creation():
    """Test JWT token creation and verification."""
    # Create token
    token = create_access_token({"sub": "testuser"})
    
    # Verify token
    assert token is not None
    assert isinstance(token, str)
    
    # Verify token contents
    payload = verify_token(token)
    assert payload["sub"] == "testuser"
    assert "exp" in payload

def test_token_verification():
    """Test JWT token verification."""
    # Create token
    token = create_access_token({"sub": "testuser"})
    
    # Verify valid token
    payload = verify_token(token)
    assert payload is not None
    assert payload["sub"] == "testuser"
    
    # Verify invalid token
    with pytest.raises(Exception):
        verify_token("invalid_token")

def test_token_expiration():
    """Test JWT token expiration."""
    # Create token with short expiration
    settings = get_settings()
    original_expire = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    settings.ACCESS_TOKEN_EXPIRE_MINUTES = 0.0001  # Set to 6 milliseconds
    
    token = create_access_token({"sub": "testuser"})
    
    # Wait for token to expire
    import time
    time.sleep(0.01)  # Wait 10 milliseconds
    
    # Verify expired token
    with pytest.raises(Exception):
        verify_token(token)
    
    # Restore original expiration
    settings.ACCESS_TOKEN_EXPIRE_MINUTES = original_expire 