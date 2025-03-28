"""
Database module for the application.
Provides database connection, models, migrations, and utilities.
"""

from src.core.database.engine import engine, async_session
from src.core.database.base import Base, init_db, get_session, get_session_context, DatabaseSession
from src.core.database.session import get_db
from src.core.database.models import User, Camera, FaceEncoding, AccessLog, Recognition, Person

__all__ = [
    'Base',
    'init_db',
    'get_session',
    'get_session_context',
    'DatabaseSession',
    'engine',
    'async_session',
    'get_db',
    # Models
    'User',
    'Camera',
    'FaceEncoding',
    'AccessLog',
    'Recognition',
    'Person'
] 
