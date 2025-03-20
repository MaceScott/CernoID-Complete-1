"""
Zone model for managing security zones.
"""

from typing import List, Optional
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from .base import BaseModel

class Zone(BaseModel):
    """Zone model for managing security zones."""
    
    __tablename__ = 'zones'

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    level = Column(Integer, default=1)
    description = Column(String)
    created_by = Column(String, ForeignKey('users.id'), nullable=False)
    updated_by = Column(String, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    creator = relationship('User', foreign_keys=[created_by], back_populates='zones')
    updater = relationship('User', foreign_keys=[updated_by])
    access_points = relationship('AccessPoint', back_populates='zone')

    def to_dict(self) -> dict:
        """Convert zone to dictionary with additional fields."""
        data = super().to_dict()
        data['level'] = self.level
        data['description'] = self.description
        return data 