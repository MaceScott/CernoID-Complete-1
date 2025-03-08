from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.config.settings import get_settings
from src.core.database.models import User
from src.api.schemas.auth import UserCreate, TokenResponse

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        query = select(User).where(User.username == username)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user

    async def create_user(self, user: UserCreate) -> User:
        db_user = User(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            hashed_password=self.get_password_hash(user.password),
            is_active=user.is_active,
            is_superuser=user.is_superuser
        )
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user

    async def get_user_by_username(self, username: str) -> Optional[User]:
        query = select(User).where(User.username == username)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none() 