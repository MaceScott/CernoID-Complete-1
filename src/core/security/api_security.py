from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
from core.error_handling import handle_exceptions
from core.utils.logging import get_logger
from core.utils.config import get_settings

security_logger = get_logger(__name__)
config = get_settings()

class SecurityManager:
    def __init__(self):
        self.security = HTTPBearer()
        self.secret_key = self.config.get('security.jwt_secret')
        self.algorithm = "HS256"
        self.access_token_expire = timedelta(minutes=30)
        self.refresh_token_expire = timedelta(days=7)

    @handle_exceptions(logger=security_logger.error)
    async def create_access_token(self, data: Dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + self.access_token_expire
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    async def verify_token(
        self, 
        credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())
    ) -> Dict:
        try:
            payload = jwt.decode(
                credentials.credentials,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            if payload.get("exp") < datetime.utcnow().timestamp():
                raise HTTPException(
                    status_code=401,
                    detail="Token has expired"
                )
            return payload
        except jwt.JWTError:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials"
            )

    @handle_exceptions(logger=security_logger.error)
    async def encrypt_sensitive_data(self, data: str) -> str:
        from cryptography.fernet import Fernet
        key = self.config.get('security.encryption_key')
        f = Fernet(key)
        return f.encrypt(data.encode()).decode()

    async def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        from cryptography.fernet import Fernet
        try:
            key = self.config.get('security.encryption_key')
            f = Fernet(key)
            decrypted_data = f.decrypt(encrypted_data.encode()).decode()
            security_logger.info("Sensitive data decrypted successfully")
            return decrypted_data
        except Exception as e:
            security_logger.error(f"Sensitive data decryption failed: {str(e)}")
            raise 