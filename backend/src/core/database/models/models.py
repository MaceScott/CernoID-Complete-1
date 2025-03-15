"""Database models."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Float, JSON, ARRAY
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.orm import relationship
from .base import Base, BaseModel

class User(BaseModel):
    """User model."""
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="user")
    permissions = Column(ARRAY(String), nullable=False, default=[])
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    face_encodings = relationship(
        "FaceEncoding",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    access_logs = relationship(
        "AccessLog",
        back_populates="user",
        passive_deletes=True
    )

class FaceEncoding(BaseModel):
    """Face encoding model."""
    __tablename__ = "face_encodings"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    encoding_data = Column(BYTEA, nullable=False)
    label = Column(String(100), nullable=False)
    confidence = Column(Float, default=0.0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="face_encodings")

class AccessLog(BaseModel):
    """Access log model."""
    __tablename__ = "access_logs"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default='now()')
    action = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
    details = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="access_logs") 