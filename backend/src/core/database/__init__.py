"""Database module initialization."""
from .models import Base, metadata
from .connection import DatabasePool

# Create a singleton database pool instance
db_pool = DatabasePool()

__all__ = [
    'Base',
    'metadata',
    'DatabasePool',
    'db_pool'
] 
