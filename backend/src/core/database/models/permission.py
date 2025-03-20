"""
Permission model for role-based access control.
"""

from typing import List, Optional
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from .base import BaseModel

class Permission(BaseModel):
    """Permission model for role-based access control."""
    
    __tablename__ = 'permissions'

    id = Column(String, primary_key=True)
    role = Column(String, nullable=False)
    resource = Column(String, nullable=False)
    action = Column(String, nullable=False)
    location = Column(String)
    created_by = Column(String, ForeignKey('users.id'), nullable=False)
    updated_by = Column(String, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    creator = relationship('User', foreign_keys=[created_by])
    updater = relationship('User', foreign_keys=[updated_by])
    users = relationship('User', secondary='user_permissions', back_populates='permissions')

    def to_dict(self) -> dict:
        """Convert permission to dictionary with additional fields."""
        data = super().to_dict()
        data['role'] = self.role
        data['resource'] = self.resource
        data['action'] = self.action
        data['location'] = self.location
        return data 