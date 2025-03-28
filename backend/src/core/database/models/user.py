"""
User model for authentication and user management.
"""

from typing import List, Optional
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..base import Base

# Association table for user permissions
user_permissions = Table(
    'user_permissions',
    Base.metadata,
    Column('user_id', String, ForeignKey('users.id'), primary_key=True),
    Column('permission_id', String, ForeignKey('permissions.id'), primary_key=True)
)

class User(Base):
    """User model for authentication and user management."""
    
    __tablename__ = 'users'

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    last_login = Column(DateTime)
    
    # Relationships
    permissions = relationship('Permission', secondary=user_permissions, back_populates='users')
    cameras = relationship('Camera', back_populates='creator')
    recognitions = relationship('Recognition', back_populates='user')
    zones = relationship('Zone', back_populates='creator')
    access_points = relationship('AccessPoint', back_populates='creator')
    assigned_alerts = relationship('Alert', foreign_keys='Alert.assigned_to', back_populates='assigned_user')
    created_alerts = relationship('Alert', foreign_keys='Alert.created_by', back_populates='creator')

    @classmethod
    async def get_by_username(cls, username: str, db: AsyncSession) -> Optional['User']:
        """Get user by username (email)."""
        query = select(cls).where(cls.email == username)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        return any(p.name == permission for p in self.permissions)

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return any(p.role == role for p in self.permissions)
        
    def to_dict(self) -> dict:
        """Convert user to dictionary."""
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'is_superuser': self.is_superuser,
            'last_login': self.last_login.isoformat() if self.last_login else None
        } 