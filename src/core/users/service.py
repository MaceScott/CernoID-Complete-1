"""
User management service with role-based access control.
"""
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import asyncpg
from pydantic import EmailStr

from ...utils.config import get_settings
from ...utils.logging import get_logger
from ..security.auth import auth_service
from ..interfaces.security import AuditInterface

class UserService:
    """User management service implementation"""
    
    def __init__(self, audit: AuditInterface):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.audit = audit
        self.pool: Optional[asyncpg.Pool] = None
        
    async def initialize(self) -> None:
        """Initialize database connection pool."""
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                self.settings.database_url,
                min_size=5,
                max_size=20
            )
            await self._ensure_tables()
            
    async def _ensure_tables(self) -> None:
        """Ensure required tables exist."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(64) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(32) NOT NULL,
                    permissions JSONB NOT NULL DEFAULT '[]',
                    is_active BOOLEAN NOT NULL DEFAULT true,
                    last_login TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
                CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
                CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
                
                CREATE TABLE IF NOT EXISTS roles (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(32) UNIQUE NOT NULL,
                    permissions JSONB NOT NULL DEFAULT '[]',
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                );
                
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    token_hash VARCHAR(255) NOT NULL,
                    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    UNIQUE (user_id, token_hash)
                );
                
                CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id 
                ON user_sessions(user_id);
                CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at 
                ON user_sessions(expires_at);
            """)
            
    async def create_user(self,
                         username: str,
                         email: EmailStr,
                         password: str,
                         role: str,
                         permissions: List[str] = []
                         ) -> Dict[str, Any]:
        """Create new user."""
        try:
            async with self.pool.acquire() as conn:
                user = await conn.fetchrow("""
                    INSERT INTO users (
                        username, email, password_hash, role, permissions
                    ) VALUES ($1, $2, $3, $4, $5)
                    RETURNING id, username, email, role, permissions,
                              is_active, last_login
                    """,
                    username,
                    email,
                    auth_service.create_password_hash(password),
                    role,
                    permissions
                )
                
                await self.audit.log_event(
                    event_type="user_management",
                    user_id=None,
                    resource="users",
                    action="create",
                    details={"user_id": user["id"]}
                )
                
                return dict(user)
                
        except asyncpg.UniqueViolationError:
            self.logger.error(f"Username or email already exists: {username}")
            raise ValueError("Username or email already exists")
        except Exception as e:
            self.logger.error(f"User creation failed: {str(e)}")
            raise
            
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            async with self.pool.acquire() as conn:
                user = await conn.fetchrow("""
                    SELECT id, username, email, role, permissions,
                           is_active, last_login
                    FROM users
                    WHERE id = $1
                    """,
                    user_id
                )
                
                return dict(user) if user else None
                
        except Exception as e:
            self.logger.error(f"User retrieval failed: {str(e)}")
            raise
            
    async def update_user(self,
                         user_id: int,
                         updates: Dict[str, Any]
                         ) -> Optional[Dict[str, Any]]:
        """Update user."""
        try:
            # Prepare update query
            set_clauses = []
            values = []
            for i, (key, value) in enumerate(updates.items(), start=1):
                set_clauses.append(f"{key} = ${i}")
                values.append(value)
                
            if not set_clauses:
                return await self.get_user(user_id)
                
            # Add updated_at timestamp
            set_clauses.append("updated_at = NOW()")
            
            async with self.pool.acquire() as conn:
                user = await conn.fetchrow(f"""
                    UPDATE users
                    SET {', '.join(set_clauses)}
                    WHERE id = ${len(values) + 1}
                    RETURNING id, username, email, role, permissions,
                              is_active, last_login
                    """,
                    *values,
                    user_id
                )
                
                if user:
                    await self.audit.log_event(
                        event_type="user_management",
                        user_id=None,
                        resource="users",
                        action="update",
                        details={
                            "user_id": user_id,
                            "updates": updates
                        }
                    )
                    
                return dict(user) if user else None
                
        except Exception as e:
            self.logger.error(f"User update failed: {str(e)}")
            raise
            
    async def delete_user(self, user_id: int) -> bool:
        """Delete user."""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute("""
                    DELETE FROM users
                    WHERE id = $1
                    """,
                    user_id
                )
                
                success = result == "DELETE 1"
                
                if success:
                    await self.audit.log_event(
                        event_type="user_management",
                        user_id=None,
                        resource="users",
                        action="delete",
                        details={"user_id": user_id}
                    )
                    
                return success
                
        except Exception as e:
            self.logger.error(f"User deletion failed: {str(e)}")
            raise
            
    async def list_users(self,
                        skip: int = 0,
                        limit: int = 100,
                        filters: Optional[Dict[str, Any]] = None
                        ) -> List[Dict[str, Any]]:
        """List users with pagination and filtering."""
        try:
            # Prepare filter conditions
            where_clauses = []
            values = []
            if filters:
                for i, (key, value) in enumerate(filters.items(), start=1):
                    where_clauses.append(f"{key} = ${i}")
                    values.append(value)
                    
            where_sql = (
                f"WHERE {' AND '.join(where_clauses)}"
                if where_clauses else ""
            )
            
            async with self.pool.acquire() as conn:
                users = await conn.fetch(f"""
                    SELECT id, username, email, role, permissions,
                           is_active, last_login
                    FROM users
                    {where_sql}
                    ORDER BY id
                    LIMIT ${len(values) + 1} OFFSET ${len(values) + 2}
                    """,
                    *values,
                    limit,
                    skip
                )
                
                return [dict(user) for user in users]
                
        except Exception as e:
            self.logger.error(f"User listing failed: {str(e)}")
            raise
            
    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self.pool:
            await self.pool.close()

# Global user service instance
user_service = UserService() 