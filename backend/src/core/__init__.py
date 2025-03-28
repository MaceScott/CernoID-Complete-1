"""Core module initialization."""
from src.core.logging.base import get_logger, setup_basic_logging
from src.core.base import BaseComponent
from src.core.database import Base, init_db, get_session, get_session_context, DatabaseSession
from src.core.database.models import User, Camera, FaceEncoding, AccessLog, Recognition, Person

__all__ = [
    'setup_basic_logging',
    'get_logger',
    'BaseComponent',
    'Base',
    'init_db',
    'get_session',
    'get_session_context',
    'DatabaseSession',
    'User',
    'Camera',
    'FaceEncoding',
    'AccessLog',
    'Recognition',
    'Person'
]
