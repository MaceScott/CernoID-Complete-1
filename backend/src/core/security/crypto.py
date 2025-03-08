from typing import Optional, Dict, Any
import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from ..base import BaseComponent
from ..utils.errors import AuthenticationError
from ..logging import get_logger

logger = get_logger(__name__)

class CryptoManager(BaseComponent):
    """Cryptographic operations manager"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._fernet: Optional[Fernet] = None
        self._key: Optional[bytes] = None

    async def initialize(self) -> None:
        """Initialize crypto manager"""
        try:
            await self._load_key()
            self._fernet = Fernet(self._key)
            logger.info("Crypto manager initialized successfully")
        except Exception as e:
            logger.error(f"Crypto manager initialization failed: {str(e)}")
            raise

    async def cleanup(self) -> None:
        """Cleanup crypto manager"""
        self._fernet = None
        self._key = None
        logger.info("Crypto manager cleaned up")

    def encrypt(self, data: str) -> str:
        """Encrypt data"""
        if not self._fernet:
            raise AuthenticationError("Crypto manager not initialized")
            
        try:
            return self._fernet.encrypt(data.encode()).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise AuthenticationError(f"Encryption failed: {str(e)}")

    def decrypt(self, data: str) -> str:
        """Decrypt data"""
        if not self._fernet:
            raise AuthenticationError("Crypto manager not initialized")
            
        try:
            return self._fernet.decrypt(data.encode()).decode()
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise AuthenticationError(f"Decryption failed: {str(e)}")

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
        logger.warning("Generated new encryption key")
        return key

    def _load_key_from_file(self, path: str) -> bytes:
        """Load key from file"""
        try:
            with open(path, 'rb') as f:
                key = base64.urlsafe_b64decode(f.read())
                logger.info(f"Key loaded successfully from file: {path}")
                return key
        except Exception as e:
            logger.error(f"Failed to load key from file {path}: {str(e)}")
            raise AuthenticationError(f"Failed to load key from file: {str(e)}")

    def _load_key_from_env(self, env_var: str) -> bytes:
        """Load key from environment variable"""
        try:
            key = base64.urlsafe_b64decode(os.environ[env_var])
            logger.info(f"Key loaded successfully from environment variable: {env_var}")
            return key
        except Exception as e:
            logger.error(f"Failed to load key from environment variable {env_var}: {str(e)}")
            raise AuthenticationError(f"Failed to load key from environment: {str(e)}")

    async def _load_key(self) -> None:
        """Load encryption key"""
        try:
            # Try to load from file first
            key_file = self.config.get('security.key_file')
            if key_file and os.path.exists(key_file):
                with open(key_file, 'rb') as f:
                    self._key = f.read()
                return
                
            # Try to load from environment
            key_env = self.config.get('security.key_env')
            if key_env and key_env in os.environ:
                self._key = base64.b64decode(os.environ[key_env])
                return
                
            # Generate new key if none found
            self._key = Fernet.generate_key()
            
        except Exception as e:
            logger.error(f"Failed to load key: {str(e)}")
            raise AuthenticationError(f"Failed to load key: {str(e)}") 