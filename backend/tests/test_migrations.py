"""Tests for database migrations."""
from sqlalchemy import inspect

def test_users_table_structure(engine):
    """Test that the users table has the correct structure."""
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

def test_migration_history_table(engine):
    """Test that the migration_history table exists."""
    inspector = inspect(engine)
    assert 'migration_history' in inspector.get_table_names()
    
    columns = {col['name']: col for col in inspector.get_columns('migration_history')}
    
    # Check required columns
    assert 'id' in columns
    assert 'version' in columns
    assert 'applied_at' in columns
    assert 'created_at' in columns
    assert 'updated_at' in columns 