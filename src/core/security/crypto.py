from typing import Optional
import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from ..utils.errors import SecurityError
from ..base import BaseComponent

class CryptoManager(BaseComponent):
    """Cryptographic operations manager"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._fernet: Optional[Fernet] = None
        self._key: Optional[bytes] = None

    async def initialize(self) -> None:
        """Initialize crypto manager"""
        key_path = self.config.get('security.key_path')
        key_env = self.config.get('security.key_env', 'APP_ENCRYPTION_KEY')
        
        if key_path:
            self._key = self._load_key_from_file(key_path)
        elif key_env in os.environ:
            self._key = self._load_key_from_env(key_env)
        else:
            self._key = self._generate_key()
            
        self._fernet = Fernet(self._key)

    async def cleanup(self) -> None:
        """Cleanup crypto manager"""
        self._key = None
        self._fernet = None

    def encrypt(self, data: str) -> str:
        """Encrypt data"""
        if not self._fernet:
            raise SecurityError("Crypto manager not initialized")
            
        try:
            return self._fernet.encrypt(
                data.encode()
            ).decode()
        except Exception as e:
            raise SecurityError(f"Encryption failed: {str(e)}")

    def decrypt(self, data: str) -> str:
        """Decrypt data"""
        if not self._fernet:
            raise SecurityError("Crypto manager not initialized")
            
        try:
            return self._fernet.decrypt(
                data.encode()
            ).decode()
        except Exception as e:
            raise SecurityError(f"Decryption failed: {str(e)}")

    def _generate_key(self) -> bytes:
        """Generate new encryption key"""
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(os.urandom(32)))
        self.logger.warning("Generated new encryption key")
        return key

    def _load_key_from_file(self, path: str) -> bytes:
        """Load key from file"""
        try:
            with open(path, 'rb') as f:
                return base64.urlsafe_b64decode(f.read())
        except Exception as e:
            raise SecurityError(f"Failed to load key from file: {str(e)}")

    def _load_key_from_env(self, env_var: str) -> bytes:
        """Load key from environment variable"""
        try:
            return base64.urlsafe_b64decode(os.environ[env_var])
        except Exception as e:
            raise SecurityError(
                f"Failed to load key from environment: {str(e)}"
            ) 