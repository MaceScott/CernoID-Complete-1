"""Database models."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from .base import BaseModel

class User(BaseModel):
    """User model for authentication and authorization."""
    __tablename__ = 'users'
    
    username = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False)
    is_superuser = Column(Boolean, nullable=False)

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"

__all__ = ['User'] 