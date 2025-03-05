"""Database models."""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean, JSON
from sqlalchemy.orm import relationship
from .models.base import BaseModel

class User(BaseModel):
    """User model for authentication and authorization."""
    __tablename__ = 'users'
    
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    role = Column(String(20), nullable=False, default='user')
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    face_encodings = relationship("FaceEncoding", back_populates="user")
    last_seen = Column(DateTime)
    metadata = Column(JSON)

class FaceEncoding(BaseModel):
    """Face encoding model for storing face recognition data."""
    __tablename__ = 'face_encodings'
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    encoding_data = Column(JSON, nullable=False)
    confidence_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="face_encodings")

class AccessLog(BaseModel):
    """Access log model for tracking system access."""
    __tablename__ = 'access_logs'
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    access_time = Column(DateTime, default=datetime.utcnow)
    access_type = Column(String(20), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    status = Column(String(20), nullable=False)
    details = Column(JSON)

# Additional models to be implemented:
# - EventLog
# - SystemSettings
# - Camera
# - Alert
# - AccessControl 