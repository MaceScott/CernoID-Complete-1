"""Tests for database functionality."""
import os
import sys
import pytest
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import Session
from core.database.models.models import User

def test_database_connection():
    """Test database connection and table structure."""
    engine = create_engine('postgresql://postgres:postgres@db:5432/cernoid')
    
    # Test connection and table existence
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert 'users' in tables
    
    # Test table structure
    columns = {col['name']: col for col in inspector.get_columns('users')}
    assert 'id' in columns
    assert 'username' in columns
    assert 'email' in columns
    assert 'hashed_password' in columns
    assert 'is_active' in columns
    assert 'is_superuser' in columns
    assert 'created_at' in columns
    assert 'updated_at' in columns

def test_user_crud_operations():
    """Test CRUD operations on User model."""
    engine = create_engine('postgresql://postgres:postgres@db:5432/cernoid')
    
    with Session(engine) as session:
        # Create
        user = User(
            username="testuser2",
            email="test2@example.com",
            hashed_password="hashedpassword123",
            is_active=True,
            is_superuser=False
        )
        session.add(user)
        session.commit()
        assert user.id is not None
        
        # Read
        queried_user = session.query(User).filter_by(username="testuser2").first()
        assert queried_user is not None
        assert queried_user.email == "test2@example.com"
        
        # Update
        queried_user.email = "updated2@example.com"
        session.commit()
        updated_user = session.query(User).filter_by(id=queried_user.id).first()
        assert updated_user.email == "updated2@example.com"
        
        # Delete
        session.delete(queried_user)
        session.commit()
        deleted_user = session.query(User).filter_by(id=queried_user.id).first()
        assert deleted_user is None

def test_user_timestamps():
    """Test that timestamps are automatically set."""
    engine = create_engine('postgresql://postgres:postgres@db:5432/cernoid')
    
    with Session(engine) as session:
        # Create user
        user = User(
            username="timeuser",
            email="time@example.com",
            hashed_password="hashedpassword123",
            is_active=True,
            is_superuser=False
        )
        session.add(user)
        session.commit()
        
        # Check timestamps
        assert user.created_at is not None
        assert user.updated_at is not None
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
        
        # Update user and check updated_at
        original_updated_at = user.updated_at
        user.email = "timeupdate@example.com"
        session.commit()
        assert user.updated_at > original_updated_at
        
        # Clean up
        session.delete(user)
        session.commit()

if __name__ == "__main__":
    pytest.main([__file__, '-v']) 