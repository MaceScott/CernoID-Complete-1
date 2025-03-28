"""Tests for database migrations."""
import pytest
import pytest_asyncio
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncEngine
from src.core.database.models import User, Person, FaceEncoding, AccessLog, Camera, Recognition

@pytest.mark.asyncio
async def test_users_table_structure(engine: AsyncEngine):
    """Test that the users table has the correct structure."""
    async with engine.connect() as conn:
        inspector = inspect(engine)
        columns = {col['name']: col for col in inspector.get_columns('users')}
        
        # Check that all required columns exist
        assert 'id' in columns
        assert 'username' in columns
        assert 'email' in columns
        assert 'hashed_password' in columns
        assert 'is_active' in columns
        assert 'is_superuser' in columns
        assert 'created_at' in columns
        assert 'updated_at' in columns

        # Check column types and properties
        assert str(columns['id']['type']) == 'INTEGER'
        assert columns['id']['primary_key'] is True
        
        assert str(columns['username']['type']) == 'VARCHAR(50)'
        assert columns['username']['nullable'] is False
        
        assert str(columns['email']['type']) == 'VARCHAR(255)'
        assert columns['email']['nullable'] is False
        
        assert str(columns['hashed_password']['type']) == 'VARCHAR(255)'
        assert columns['hashed_password']['nullable'] is False
        
        assert str(columns['is_active']['type']) == 'BOOLEAN'
        assert columns['is_active']['nullable'] is False
        
        assert str(columns['is_superuser']['type']) == 'BOOLEAN'
        assert columns['is_superuser']['nullable'] is False
        
        assert str(columns['created_at']['type']) == 'TIMESTAMP'
        assert columns['created_at']['nullable'] is False
        
        assert str(columns['updated_at']['type']) == 'TIMESTAMP'
        assert columns['updated_at']['nullable'] is False

@pytest.mark.asyncio
async def test_migration_history_table(engine: AsyncEngine):
    """Test that the alembic_version table exists."""
    async with engine.connect() as conn:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        assert 'alembic_version' in tables
        
        columns = {col['name']: col for col in inspector.get_columns('alembic_version')}
        
        # Check required columns
        assert 'id' in columns
        assert 'version' in columns
        assert 'applied_at' in columns
        assert 'created_at' in columns
        assert 'updated_at' in columns 