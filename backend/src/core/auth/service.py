"""Authentication service."""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from core.config import Settings
from core.database.models.models import User
from core.auth.schemas import UserCreate, UserRead

settings = Settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """Authentication service."""

    def __init__(self):
        """Initialize auth service."""
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password."""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Get password hash."""
        return pwd_context.hash(password)

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user."""
        user = await User.get_by_username(username)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user

    def create_access_token(self, data: dict) -> str:
        """Create access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    async def create_user(self, user_data: UserCreate) -> UserRead:
        """Create new user."""
        # Check if username exists
        if await User.get_by_username(user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email exists
        if await User.get_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user
        hashed_password = self.get_password_hash(user_data.password)
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            is_active=True
        )
        await user.save()
        return UserRead.from_orm(user) 