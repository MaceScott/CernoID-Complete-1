"""
Camera model for managing security cameras.
"""

from typing import List, Optional
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from ..base import Base

class Camera(Base):
    """Camera model for managing security cameras."""
    
    __tablename__ = 'cameras'

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    location = Column(String)
    status = Column(String, default='offline')
    settings = Column(JSON)
    created_by = Column(String, ForeignKey('users.id'), nullable=False)
    updated_by = Column(String, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    creator = relationship('User', foreign_keys=[created_by], back_populates='cameras')
    updater = relationship('User', foreign_keys=[updated_by])
    recognitions = relationship('Recognition', back_populates='camera')
    alerts = relationship('Alert', back_populates='camera')

    def to_dict(self) -> dict:
        """Convert camera to dictionary with additional fields."""
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'location': self.location,
            'status': self.status,
            'settings': self.settings,
            'created_by': self.created_by,
            'updated_by': self.updated_by
        } 