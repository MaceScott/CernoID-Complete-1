from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
from ..database import DatabasePool

class AuthManager:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.db_pool = DatabasePool()
        self.secret_key = "your-secret-key"  # Move to config

    async def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        async with self.db_pool.get_connection() as conn:
            user = await conn.execute(
                "SELECT * FROM users WHERE username = $1", 
                username
            )
            if user and self.pwd_context.verify(password, user['password']):
                return self._create_token(user)
        return None

    def _create_token(self, user: dict) -> dict:
        expires = datetime.utcnow() + timedelta(hours=24)
        token = jwt.encode(
            {
                'user_id': user['id'],
                'exp': expires
            },
            self.secret_key,
            algorithm='HS256'
        )
        return {
            'access_token': token,
            'token_type': 'bearer',
            'expires': expires
        }
