from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean, JSON
from sqlalchemy.orm import relationship

from .models.base import BaseModel

class User(BaseModel):
    """User model for authentication and authorization."""
    __tablename__ = 'users'
    
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)
    face_encodings = relationship("FaceEncoding", back_populates="user")
    last_seen = Column(DateTime)
    metadata = Column(JSON)

class FaceEncoding(BaseModel):
    """Face encoding storage"""
    __tablename__ = 'face_encodings'
    
    user_id = Column(Integer, ForeignKey('users.id'))
    encoding = Column(JSON, nullable=False)  # Store as JSON array
    quality_score = Column(Float)
    metadata = Column(JSON)
    user = relationship("User", back_populates="face_encodings")

class AccessLog(BaseModel):
    """Access logging for security"""
    __tablename__ = 'access_logs'
    
    person_id = Column(Integer, ForeignKey('persons.id'))
    camera_id = Column(String(50))
    confidence_score = Column(Float)
    access_granted = Column(Boolean)
    person = relationship("Person", back_populates="access_logs")

# Additional models to be implemented:
# - EventLog
# - SystemSettings
# - Camera
# - Alert
# - AccessControl 