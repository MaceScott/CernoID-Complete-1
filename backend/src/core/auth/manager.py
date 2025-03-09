"""
Authentication manager for handling user authentication and authorization.
"""
from typing import Dict, Optional
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import Settings
from core.database.models.models import User
from .schemas import TokenData

settings = Settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthManager:
    """Handles user authentication and authorization."""
    
    def __init__(self):
        """Initialize auth manager."""
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
            
    async def get_current_user(self, token: str, db: AsyncSession) -> Optional[User]:
        """Get current user from token."""
        try:
            payload = await self.verify_token(token)
            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            # Get user from database
            user = await db.get(User, int(user_id))
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return user
        except Exception as e:
            logger.error(f"Failed to get current user: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            ) 