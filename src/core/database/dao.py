from typing import List, Optional, Type, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from core.database.models import Base
import logging

class BaseDAO:
    """Base Data Access Object for database operations"""
    
    def __init__(self, session: AsyncSession, model: Type[Base]):
        self.session = session
        self.model = model

    async def create(self, **kwargs) -> Base:
        """Create a new record"""
        try:
            instance = self.model(**kwargs)
            self.session.add(instance)
            await self.session.commit()
            await self.session.refresh(instance)
            logging.info(f"Record created successfully: {instance}")
            return instance
        except Exception as e:
            logging.error(f"Failed to create record: {str(e)}")
            raise

    async def get_by_id(self, id: int) -> Optional[Base]:
        """Get record by ID"""
        query = select(self.model).where(self.model.id == id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(self) -> List[Base]:
        """Get all records"""
        query = select(self.model)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update(self, id: int, **kwargs) -> Optional[Base]:
        """Update a record"""
        query = update(self.model)\
            .where(self.model.id == id)\
            .values(**kwargs)\
            .returning(self.model)
        result = await self.session.execute(query)
        await self.session.commit()
        return result.scalar_one_or_none()

    async def delete(self, id: int) -> bool:
        """Delete a record"""
        query = delete(self.model).where(self.model.id == id)
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0 