"""Database models."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Float, JSON, ARRAY, LargeBinary
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select
from typing import Optional
from .base import BaseModel

class User(BaseModel):
    """User model."""
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="user")
    permissions = Column(JSON, nullable=False, default=list)
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
    recognitions = relationship(
        "Recognition",
        back_populates="user",
        passive_deletes=True
    )

    @classmethod
    async def get_by_username(cls, username: str, db: AsyncSession) -> Optional['User']:
        """Get user by username (email)."""
        query = select(cls).where(cls.email == username)
        result = await db.execute(query)
        return result.scalar_one_or_none()

class Camera(BaseModel):
    """Camera model."""
    __tablename__ = "cameras"
    
    name = Column(String(100), nullable=False)
    location = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 addresses can be up to 45 chars
    port = Column(Integer, nullable=True)
    username = Column(String(100), nullable=True)
    password = Column(String(255), nullable=True)
    stream_url = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    settings = Column(JSON, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    
    # Relationships
    recognitions = relationship(
        "Recognition",
        back_populates="camera",
        passive_deletes=True
    )

class FaceEncoding(BaseModel):
    """Face encoding model."""
    __tablename__ = "face_encodings"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    encoding_data = Column(LargeBinary, nullable=False)
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

class Recognition(BaseModel):
    """Recognition model for tracking face recognition events."""
    __tablename__ = "recognitions"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    face_id = Column(Integer, ForeignKey("face_encodings.id", ondelete="CASCADE"), nullable=False)
    confidence = Column(Float, nullable=False)
    meta_info = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="recognitions")
    face = relationship("FaceEncoding")

    @classmethod
    async def get_by_id(cls, db, recognition_id: str):
        """Get recognition by ID."""
        return await db.query(cls).filter(cls.id == recognition_id).first()

    async def update_recognition(self, db, **kwargs):
        """Update recognition details."""
        for key, value in kwargs.items():
            setattr(self, key, value)
        await db.commit()

class Person(BaseModel):
    """Person model."""
    __tablename__ = "persons"

    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20), nullable=True)
    department = Column(String(100), nullable=True)
    position = Column(String(100), nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    face_encodings = relationship(
        "FaceEncoding",
        back_populates="person",
        cascade="all, delete-orphan"
    )
    access_logs = relationship(
        "AccessLog",
        back_populates="person",
        passive_deletes=True
    )
    recognitions = relationship(
        "Recognition",
        back_populates="person",
        passive_deletes=True
    ) 