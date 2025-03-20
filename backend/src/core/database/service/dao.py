"""
Data Access Object (DAO) service for database operations.
Provides base CRUD operations for all models.
"""

from typing import List, Optional, Type, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, and_
from sqlalchemy.orm import selectinload
from ...utils.logging import get_logger
from ..models import Base

logger = get_logger(__name__)

class BaseDAO:
    """Base Data Access Object for database operations"""
    
    def __init__(self, session: AsyncSession, model: Type[Base]):
        self.session = session
        self.model = model
        self.logger = get_logger(f"{__name__}.{model.__name__}")

    async def create(self, **kwargs) -> Base:
        """Create a new record"""
        try:
            instance = self.model(**kwargs)
            self.session.add(instance)
            await self.session.commit()
            await self.session.refresh(instance)
            self.logger.info(f"Created {self.model.__name__}: {instance.id}")
            return instance
        except Exception as e:
            self.logger.error(f"Failed to create {self.model.__name__}: {str(e)}")
            await self.session.rollback()
            raise

    async def get_by_id(self, id: Any, load_relationships: bool = False) -> Optional[Base]:
        """Get record by ID"""
        try:
            query = select(self.model).where(self.model.id == id)
            if load_relationships:
                query = query.options(selectinload(*self.model.__mapper__.relationships))
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            self.logger.error(f"Failed to get {self.model.__name__} by ID {id}: {str(e)}")
            raise

    async def get_all(self, load_relationships: bool = False) -> List[Base]:
        """Get all records"""
        try:
            query = select(self.model)
            if load_relationships:
                query = query.options(selectinload(*self.model.__mapper__.relationships))
            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e:
            self.logger.error(f"Failed to get all {self.model.__name__}s: {str(e)}")
            raise

    async def get_by_criteria(self, criteria: Dict[str, Any], load_relationships: bool = False) -> List[Base]:
        """Get records by criteria"""
        try:
            conditions = [getattr(self.model, key) == value for key, value in criteria.items()]
            query = select(self.model).where(and_(*conditions))
            if load_relationships:
                query = query.options(selectinload(*self.model.__mapper__.relationships))
            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e:
            self.logger.error(f"Failed to get {self.model.__name__}s by criteria: {str(e)}")
            raise

    async def update(self, id: Any, **kwargs) -> Optional[Base]:
        """Update a record"""
        try:
            query = update(self.model)\
                .where(self.model.id == id)\
                .values(**kwargs)\
                .returning(self.model)
            result = await self.session.execute(query)
            await self.session.commit()
            instance = result.scalar_one_or_none()
            if instance:
                self.logger.info(f"Updated {self.model.__name__}: {id}")
            return instance
        except Exception as e:
            self.logger.error(f"Failed to update {self.model.__name__} {id}: {str(e)}")
            await self.session.rollback()
            raise

    async def delete(self, id: Any) -> bool:
        """Delete a record"""
        try:
            query = delete(self.model).where(self.model.id == id)
            result = await self.session.execute(query)
            await self.session.commit()
            success = result.rowcount > 0
            if success:
                self.logger.info(f"Deleted {self.model.__name__}: {id}")
            return success
        except Exception as e:
            self.logger.error(f"Failed to delete {self.model.__name__} {id}: {str(e)}")
            await self.session.rollback()
            raise

    async def exists(self, id: Any) -> bool:
        """Check if record exists"""
        try:
            query = select(self.model.id).where(self.model.id == id)
            result = await self.session.execute(query)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            self.logger.error(f"Failed to check existence of {self.model.__name__} {id}: {str(e)}")
            raise 