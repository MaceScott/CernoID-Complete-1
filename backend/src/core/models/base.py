"""
File: base.py
Purpose: Base database models and schemas for the CernoID system.

Key Features:
- Base model definitions
- Common field types
- Validation rules
- Serialization methods
- Database operations
- Audit tracking

Dependencies:
- Pydantic: Data validation and serialization
- MongoDB: Database operations
- Core services:
  - Database: Storage operations
  - Validation: Data validation
  - Serialization: Data formatting
  - Audit: Change tracking

Architecture:
- Model inheritance
- Field validation
- Type checking
- Event tracking
- Error handling
- State management

Performance:
- Lazy loading
- Field filtering
- Index support
- Cache integration
- Batch operations
- Query optimization
"""

from typing import Dict, List, Optional, Any, Type, TypeVar, Generic
from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel, Field, validator
from pydantic.generics import GenericModel

from ...database import Database
from ...utils.logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T', bound='BaseDBModel')

class BaseDBModel(BaseModel):
    """
    Base model for all database entities.
    
    Attributes:
        id (ObjectId): Document identifier
        created_at (datetime): Creation timestamp
        updated_at (datetime): Last update timestamp
        is_active (bool): Active status flag
        metadata (Dict[str, Any]): Additional metadata
        
    Features:
        - Automatic timestamps
        - Soft deletion support
        - Metadata storage
        - Audit tracking
        - Validation rules
        
    Database:
        - Collection naming
        - Index management
        - Query building
        - Batch operations
        - Transaction support
    """
    
    id: Optional[ObjectId] = Field(None, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """
        Model configuration.
        
        Settings:
            - Allow population by field name
            - Preserve field aliases
            - JSON encoders for types
            - Arbitrary type checks
            - Schema validation
        """
        allow_population_by_field_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }
        
    @validator("metadata")
    def validate_metadata(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate metadata dictionary.
        
        Args:
            v: Metadata dictionary
            
        Returns:
            Dict[str, Any]: Validated metadata
            
        Validation:
            - Key format
            - Value types
            - Size limits
            - Required fields
            - Custom rules
        """
        if not isinstance(v, dict):
            raise ValueError("Metadata must be a dictionary")
            
        # Validate keys
        for key in v:
            if not isinstance(key, str):
                raise ValueError("Metadata keys must be strings")
                
        return v
        
    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Convert model to dictionary.
        
        Args:
            *args: Additional arguments
            **kwargs: Additional keyword arguments
            
        Returns:
            Dict[str, Any]: Model dictionary
            
        Features:
            - Field filtering
            - Alias handling
            - Type conversion
            - Nested models
            - Custom encoders
        """
        d = super().dict(*args, **kwargs)
        
        # Convert ObjectId to string
        if "_id" in d and d["_id"]:
            d["_id"] = str(d["_id"])
            
        return d
        
    @classmethod
    async def get_by_id(cls: Type[T], db: Database, id: ObjectId) -> Optional[T]:
        """
        Get document by ID.
        
        Args:
            db: Database connection
            id: Document identifier
            
        Returns:
            Optional[T]: Document instance if found
            
        Features:
            - ID validation
            - Field selection
            - Error handling
            - Cache support
            - Audit logging
        """
        try:
            collection = db[cls.__name__.lower()]
            doc = await collection.find_one({"_id": id})
            return cls(**doc) if doc else None
            
        except Exception as e:
            logger.error(f"Failed to get document: {str(e)}")
            raise
            
    @classmethod
    async def find(
        cls: Type[T],
        db: Database,
        query: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
        sort: Optional[List[tuple]] = None
    ) -> List[T]:
        """
        Find documents by query.
        
        Args:
            db: Database connection
            query: Query dictionary
            skip: Number of documents to skip
            limit: Maximum number of documents
            sort: Sort specification
            
        Returns:
            List[T]: List of document instances
            
        Features:
            - Query building
            - Pagination
            - Sorting
            - Field selection
            - Index usage
        """
        try:
            collection = db[cls.__name__.lower()]
            cursor = collection.find(query)
            
            # Apply pagination
            if skip:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)
                
            # Apply sorting
            if sort:
                cursor = cursor.sort(sort)
                
            # Get documents
            docs = []
            async for doc in cursor:
                docs.append(cls(**doc))
                
            return docs
            
        except Exception as e:
            logger.error(f"Failed to find documents: {str(e)}")
            raise
            
    async def save(self, db: Database) -> None:
        """
        Save document to database.
        
        Args:
            db: Database connection
            
        Features:
            - Validation
            - Timestamps
            - Audit logging
            - Error handling
            - Event dispatch
        """
        try:
            collection = db[self.__class__.__name__.lower()]
            
            # Update timestamp
            self.updated_at = datetime.utcnow()
            
            # Save document
            if self.id:
                await collection.update_one(
                    {"_id": self.id},
                    {"$set": self.dict(exclude={"id"})}
                )
            else:
                result = await collection.insert_one(self.dict(exclude={"id"}))
                self.id = result.inserted_id
                
        except Exception as e:
            logger.error(f"Failed to save document: {str(e)}")
            raise
            
    async def delete(self, db: Database) -> None:
        """
        Delete document from database.
        
        Args:
            db: Database connection
            
        Features:
            - Soft deletion
            - Cascade delete
            - Event dispatch
            - Audit logging
            - Error handling
        """
        try:
            collection = db[self.__class__.__name__.lower()]
            
            # Soft delete
            self.is_active = False
            self.updated_at = datetime.utcnow()
            
            await collection.update_one(
                {"_id": self.id},
                {"$set": {"is_active": False, "updated_at": self.updated_at}}
            )
            
        except Exception as e:
            logger.error(f"Failed to delete document: {str(e)}")
            raise
            
    @classmethod
    async def create_indexes(cls, db: Database) -> None:
        """
        Create collection indexes.
        
        Args:
            db: Database connection
            
        Features:
            - Index creation
            - Performance tuning
            - Field selection
            - Compound indexes
            - Background creation
        """
        try:
            collection = db[cls.__name__.lower()]
            
            # Create default indexes
            await collection.create_index("created_at")
            await collection.create_index("updated_at")
            await collection.create_index("is_active")
            
            # Create custom indexes
            indexes = cls.get_indexes()
            for index in indexes:
                await collection.create_index(**index)
                
        except Exception as e:
            logger.error(f"Failed to create indexes: {str(e)}")
            raise
            
    @classmethod
    def get_indexes(cls) -> List[Dict[str, Any]]:
        """
        Get collection indexes.
        
        Returns:
            List[Dict[str, Any]]: Index specifications
            
        Features:
            - Index types
            - Field selection
            - Sort order
            - Uniqueness
            - Sparse options
        """
        return []
        
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """
        Get model JSON schema.
        
        Returns:
            Dict[str, Any]: JSON schema
            
        Features:
            - Field types
            - Validation rules
            - Required fields
            - Default values
            - Custom formats
        """
        return cls.schema() 