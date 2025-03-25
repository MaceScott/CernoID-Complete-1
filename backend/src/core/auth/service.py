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

from ..config import settings
from ..database import db_pool
from ..base import BaseComponent

logger = logging.getLogger(__name__)

class TokenData(BaseModel):
    """Token data model."""
    user_id: int
    username: str
    role: str
    exp: datetime

class AuthService(BaseComponent):
    """Authentication service."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            super().__init__(settings.dict())
            self._initialized = True
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

    async def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create access token."""
        try:
            to_encode = data.copy()
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

    async def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user."""
        try:
            # Get user from database
            query = "SELECT id, username, password, role FROM users WHERE username = $1"
            user = await db_pool.fetchrow(query, username)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password"
                )
            
            # Verify password
            if not await self.verify_password(password, user['password']):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password"
                )
            
            # Create access token
            access_token = await self.create_access_token({
                "user_id": user['id'],
                "username": user['username'],
                "role": user['role']
            })
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user['id'],
                    "username": user['username'],
                    "role": user['role']
                }
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication failed"
            ) 