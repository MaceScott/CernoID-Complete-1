"""
Database service with connection pooling and transaction management.
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update, delete
from contextlib import asynccontextmanager
import json
import asyncpg

from .models import Base, User, FaceEncoding
from ..utils.config import get_settings
from ..utils.logging import get_logger
from ..interfaces.security import EncryptionInterface

class DatabaseService:
    """
    Async database service with connection pooling
    """
    
    def __init__(self, encryption: EncryptionInterface):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.encryption = encryption
        
        # Create async engine
        self.engine = create_async_engine(
            self.settings.database_url,
            echo=self.settings.sql_debug,
            pool_size=self.settings.db_pool_size,
            max_overflow=self.settings.db_max_overflow,
            pool_timeout=self.settings.db_pool_timeout
        )
        
        # Create session factory
        self.async_session = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Initialize connection pool
        self.pool = None
        
    @asynccontextmanager
    async def session(self) -> AsyncSession:
        """Get database session with automatic cleanup."""
        session = self.async_session()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            self.logger.error(f"Database error: {str(e)}")
            raise
        finally:
            await session.close()
            
    async def initialize(self):
        """Initialize database connection pool."""
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                self.settings.database_url,
                min_size=5,
                max_size=20
            )
            
    async def cleanup(self):
        """Cleanup database connections."""
        await self.engine.dispose()
        
    # User operations
    async def create_user(self, user_data: Dict) -> User:
        """Create new user."""
        async with self.session() as session:
            user = User(**user_data)
            session.add(user)
            await session.flush()
            return user
            
    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        async with self.session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()
            
    async def update_user(self,
                         user_id: int,
                         update_data: Dict) -> Optional[User]:
        """Update user data."""
        async with self.session() as session:
            result = await session.execute(
                update(User)
                .where(User.id == user_id)
                .values(**update_data)
                .returning(User)
            )
            return result.scalar_one_or_none()
            
    # Face encoding operations
    async def create_encoding(self,
                            encoding_data: Dict) -> FaceEncoding:
        """Create new face encoding."""
        async with self.session() as session:
            encoding = FaceEncoding(**encoding_data)
            session.add(encoding)
            await session.flush()
            return encoding
            
    async def get_user_encodings(self,
                                user_id: int) -> List[FaceEncoding]:
        """Get all encodings for user."""
        async with self.session() as session:
            result = await session.execute(
                select(FaceEncoding)
                .where(FaceEncoding.user_id == user_id)
            )
            return result.scalars().all()
            
    async def delete_encoding(self,
                            encoding_id: int) -> bool:
        """Delete face encoding."""
        async with self.session() as session:
            result = await session.execute(
                delete(FaceEncoding)
                .where(FaceEncoding.id == encoding_id)
            )
            return result.rowcount > 0
            
    # Batch operations
    async def batch_create_encodings(self,
                                   encodings: List[Dict]) -> List[FaceEncoding]:
        """Create multiple encodings in batch."""
        async with self.session() as session:
            encoding_objects = [FaceEncoding(**data) for data in encodings]
            session.add_all(encoding_objects)
            await session.flush()
            return encoding_objects
            
    # Query operations
    async def search_users(self,
                          query: Dict) -> List[User]:
        """Search users with filters."""
        async with self.session() as session:
            statement = select(User)
            
            # Apply filters
            for key, value in query.items():
                if hasattr(User, key):
                    statement = statement.where(getattr(User, key) == value)
                    
            result = await session.execute(statement)
            return result.scalars().all()
            
    async def get_recent_encodings(self,
                                 limit: int = 100) -> List[FaceEncoding]:
        """Get recent face encodings."""
        async with self.session() as session:
            result = await session.execute(
                select(FaceEncoding)
                .order_by(FaceEncoding.created_at.desc())
                .limit(limit)
            )
            return result.scalars().all()
            
    async def create_audit_event(self,
                               event: Dict[str, Any]) -> str:
        """Create audit event record."""
        try:
            # Encrypt sensitive details
            if "details" in event:
                encrypted = await self.encryption.encrypt(
                    json.dumps(event["details"]).encode()
                )
                event["details"] = encrypted
                
            async with self.pool.acquire() as conn:
                return await conn.fetchval(
                    """
                    INSERT INTO audit_events (
                        event_id, timestamp, event_type, user_id,
                        resource, action, details, status, signature
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    RETURNING event_id
                    """,
                    event["event_id"],
                    event["timestamp"],
                    event["event_type"],
                    event["user_id"],
                    event["resource"],
                    event["action"],
                    json.dumps(event["details"]),
                    event["status"],
                    event["signature"]
                )
                
        except Exception as e:
            self.logger.error(f"Failed to create audit event: {str(e)}")
            raise 