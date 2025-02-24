from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Union
import asyncio
import logging
import jwt
import bcrypt
import secrets
from jose import JWTError
from passlib.context import CryptContext
from core.database.models import User
from core.database.dao import BaseDAO
from fastapi import Request, Response, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import aioredis
from dataclasses import dataclass
from ..config.settings import get_settings
from ..utils.errors import AuthenticationError

@dataclass
class AuthConfig:
    """Authentication configuration"""
    secret_key: str
    token_expiration: int = 3600  # 1 hour
    refresh_token_expiration: int = 2592000  # 30 days
    token_algorithm: str = "HS256"
    password_hash_rounds: int = 12
    max_failed_attempts: int = 5
    lockout_duration: int = 900  # 15 minutes

class AuthManager:
    """Authentication and authorization management"""
    
    def __init__(self):
        self.settings = get_settings()
        self.secret_key = self.settings.jwt_secret_key
        self.token_expire_minutes = self.settings.token_expire_minutes
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.logger = logging.getLogger('AuthManager')
        self._redis: Optional[aioredis.Redis] = None
        self._token_blacklist: set = set()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._auth_config = AuthConfig(**self.settings.auth)
        self._oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
        self._algorithm = self.settings.jwt_algorithm
        self._access_token_expire = self.settings.access_token_expire
        self._refresh_token_expire = self.settings.refresh_token_expire

    async def initialize(self) -> None:
        """Initialize authentication manager"""
        try:
            # Connect to Redis
            self._redis = await aioredis.create_redis_pool(
                self.settings.redis_url
            )
            
            # Start cleanup task
            self._cleanup_task = asyncio.create_task(
                self._cleanup_expired_tokens()
            )
            
            self.logger.info("Authentication manager initialized")
            
        except Exception as e:
            self.logger.error(
                f"Authentication manager initialization failed: {str(e)}"
            )
            raise

    async def authenticate_user(self, username: str, password: str) -> Dict:
        """Authenticate user and return user data"""
        try:
            # Add your user authentication logic here
            user = await self.verify_credentials(username, password)
            if not user:
                raise AuthenticationError("Invalid credentials")
            return user
        except Exception as e:
            raise AuthenticationError(str(e))

    def create_access_token(self, data: Dict) -> str:
        """Create JWT access token"""
        expire = datetime.utcnow() + timedelta(minutes=self.token_expire_minutes)
        to_encode = data.copy()
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm="HS256")

    def create_refresh_token(self, data: Dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self._refresh_token_expire)
        to_encode.update({"exp": expire})
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self._algorithm)

    async def verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self._algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Generate password hash"""
        return self.pwd_context.hash(password) 