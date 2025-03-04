from typing import Dict, Optional, List, Union, Any
from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel, Field, validator
from ..utils.errors import ModelError

class BaseDBModel(BaseModel):
    """Base database model"""
    
    id: str = Field(default_factory=lambda: str(ObjectId()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }
    
    @validator('id', pre=True)
    def convert_object_id(cls, v):
        """Convert ObjectId to string"""
        if isinstance(v, ObjectId):
            return str(v)
        return v

    def dict(self, *args, **kwargs) -> Dict:
        """Convert model to dictionary"""
        d = super().dict(*args, **kwargs)
        # Convert datetime objects to ISO format
        for k, v in d.items():
            if isinstance(v, datetime):
                d[k] = v.isoformat()
        return d

    async def save(self, db) -> bool:
        """Save model to database"""
        try:
            self.updated_at = datetime.utcnow()
            result = await db[self.__class__.__name__.lower()].update_one(
                {'id': self.id},
                {'$set': self.dict()},
                upsert=True
            )
            return result.acknowledged
        except Exception as e:
            raise ModelError(f"Save failed: {str(e)}")

    @classmethod
    async def find(cls, db, query: Dict) -> List['BaseDBModel']:
        """Find models matching query"""
        try:
            cursor = db[cls.__name__.lower()].find(query)
            return [cls(**doc) async for doc in cursor]
        except Exception as e:
            raise ModelError(f"Find failed: {str(e)}")

    @classmethod
    async def find_one(cls, db, query: Dict) -> Optional['BaseDBModel']:
        """Find single model matching query"""
        try:
            doc = await db[cls.__name__.lower()].find_one(query)
            return cls(**doc) if doc else None
        except Exception as e:
            raise ModelError(f"Find one failed: {str(e)}")

    async def delete(self, db) -> bool:
        """Delete model from database"""
        try:
            result = await db[self.__class__.__name__.lower()].delete_one(
                {'id': self.id}
            )
            return result.acknowledged
        except Exception as e:
            raise ModelError(f"Delete failed: {str(e)}") 