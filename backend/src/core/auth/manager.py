"""
Authentication manager for handling user authentication and authorization.
"""
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import logging

from core.config import Settings
from core.database.models.models import User
from .schemas import TokenData
from .service import AuthService

settings = Settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

logger = logging.getLogger(__name__)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

class User(BaseModel):
    """User model."""
    id: int
    username: str
    role: str

class AuthManager:
    """Authentication manager."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._auth_service = AuthService()
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
        
    def get_password_hash(self, password: str) -> str:
        """Generate password hash."""
        return pwd_context.hash(password)
        
    def create_access_token(self, data: dict) -> str:
        """Create a new access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
        
    async def verify_token(self, token: str) -> Optional[User]:
        """Verify an access token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            if username is None:
                return None
            token_data = TokenData(username=username)
        except JWTError:
            return None

        user = await User.get_by_username(token_data.username)
        if user is None:
            return None
        return user
            
    async def get_current_user(self, token: str = Depends(oauth2_scheme)) -> User:
        """Get current user from token."""
        try:
            token_data = await self._auth_service.verify_token(token)
            return User(
                id=token_data.user_id,
                username=token_data.username,
                role=token_data.role
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get current user: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )

    async def check_permissions(self, user: User, required_role: str) -> bool:
        """Check if user has required role."""
        try:
            # Admin has all permissions
            if user.role == "admin":
                return True
            
            # Check specific role
            return user.role == required_role
        except Exception as e:
            logger.error(f"Permission check failed: {e}")
            return False

# Create singleton instance
auth_manager = AuthManager()

# Dependency for getting current user
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get current user dependency."""
    return await auth_manager.get_current_user(token) 