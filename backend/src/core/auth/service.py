"""
Authentication service module.
"""
from typing import Optional, Dict, Any
import jwt
from datetime import datetime, timedelta
import bcrypt
import logging
from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config.settings import get_settings
from core.database.models.models import User
from core.base import BaseComponent

logger = logging.getLogger(__name__)

class TokenData(BaseModel):
    """Token data model."""
    user_id: int
    username: str
    role: str
    exp: datetime

class AuthService(BaseComponent):
    """Authentication service."""

    def __init__(self, settings):
        super().__init__(settings.dict())
        self._secret_key = settings.SECRET_KEY
        self._algorithm = settings.ALGORITHM
        self._access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    async def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password."""
        try:
            return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            return False

    async def get_password_hash(self, password: str) -> str:
        """Get password hash."""
        try:
            salt = bcrypt.gensalt()
            return bcrypt.hashpw(password.encode(), salt).decode()
        except Exception as e:
            logger.error(f"Password hashing failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to hash password"
            )

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create access token."""
        try:
            to_encode = data.copy()
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(minutes=self._access_token_expire_minutes)
            to_encode.update({"exp": expire})
            encoded_jwt = jwt.encode(to_encode, self._secret_key, algorithm=self._algorithm)
            return encoded_jwt
        except Exception as e:
            logger.error(f"Token creation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create access token"
            )

    async def verify_token(self, token: str) -> TokenData:
        """Verify token."""
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
            token_data = TokenData(
                user_id=payload.get("user_id"),
                username=payload.get("username"),
                role=payload.get("role"),
                exp=datetime.fromtimestamp(payload.get("exp"))
            )
            return token_data
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify token"
            )

    async def authenticate_user(self, username: str, password: str, db: AsyncSession) -> Optional[User]:
        """Authenticate user."""
        try:
            # Get user from database
            query = select(User).where(User.email == username)
            result = await db.execute(query)
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            # Verify password
            if not await self.verify_password(password, user.hashed_password):
                return None
            
            return user

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication failed"
            ) 