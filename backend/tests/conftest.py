"""Test configuration and fixtures."""
import os
import sys
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from datetime import datetime
from sqlalchemy_utils import create_database, drop_database, database_exists

# Add src directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database.models import Base, User

# Test database URL
TEST_DATABASE_URL = "postgresql://postgres:postgres@db:5432/test_cernoid"

@pytest.fixture(scope="session")
def test_db():
    """Create a test database."""
    if database_exists(TEST_DATABASE_URL):
        drop_database(TEST_DATABASE_URL)
    create_database(TEST_DATABASE_URL)
    
    # Create all tables
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    
    yield TEST_DATABASE_URL
    
    # Cleanup after tests
    drop_database(TEST_DATABASE_URL)

@pytest.fixture(scope="function")
def db_session(test_db):
    """Create a database session."""
    engine = create_engine(test_db)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    
    with Session() as session:
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

@pytest.fixture(scope="function")
def test_user(db_session):
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashedpassword123",
        is_active=True,
        is_superuser=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    yield user
    db_session.delete(user)
    db_session.commit() 