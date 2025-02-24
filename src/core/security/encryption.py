"""
Data encryption system with key management.
"""
from typing import Dict, Any, Optional, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import base64
import os
from pathlib import Path
import json

from ..utils.config import get_settings
from ..utils.logging import get_logger

class EncryptionService:
    """
    Advanced encryption service with key rotation
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        
        # Initialize key storage
        self.key_dir = Path(self.settings.key_dir)
        self.key_dir.mkdir(exist_ok=True)
        
        # Load encryption keys
        self.keys = self._load_keys()
        
        # Initialize Fernet instance with current key
        self.fernet = Fernet(self.current_key)
        
    def _load_keys(self) -> Dict[str, bytes]:
        """Load encryption keys from secure storage."""
        keys = {}
        
        try:
            for key_file in self.key_dir.glob("*.key"):
                with open(key_file, 'rb') as f:
                    key_id = key_file.stem
                    keys[key_id] = base64.urlsafe_b64decode(f.read())
                    
            if not keys:
                # Generate initial key
                key_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                keys[key_id] = self._generate_key()
                self._save_key(key_id, keys[key_id])
                
            return keys
            
        except Exception as e:
            self.logger.error(f"Key loading failed: {str(e)}")
            raise
            
    def _generate_key(self) -> bytes:
        """Generate new encryption key."""
        return Fernet.generate_key()
        
    def _save_key(self, key_id: str, key: bytes):
        """Save encryption key to secure storage."""
        key_path = self.key_dir / f"{key_id}.key"
        
        with open(key_path, 'wb') as f:
            f.write(base64.urlsafe_b64encode(key))
            
    async def rotate_key(self) -> str:
        """Rotate encryption key."""
        try:
            # Generate new key
            key_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            new_key = self._generate_key()
            
            # Save new key
            self._save_key(key_id, new_key)
            
            # Update keys dictionary
            self.keys[key_id] = new_key
            
            # Update Fernet instance
            self.fernet = Fernet(new_key)
            
            return key_id
            
        except Exception as e:
            self.logger.error(f"Key rotation failed: {str(e)}")
            raise
            
    @property
    def current_key(self) -> bytes:
        """Get current encryption key."""
        # Use most recent key
        latest_key_id = max(self.keys.keys())
        return self.keys[latest_key_id]
        
    async def encrypt(self,
                     data: Union[str, bytes],
                     key_id: Optional[str] = None) -> Dict[str, str]:
        """Encrypt data with specified key."""
        try:
            if isinstance(data, str):
                data = data.encode()
                
            # Use specified key or current key
            key = self.keys[key_id] if key_id else self.current_key
            fernet = Fernet(key)
            
            # Encrypt data
            encrypted_data = fernet.encrypt(data)
            
            return {
                "data": base64.urlsafe_b64encode(encrypted_data).decode(),
                "key_id": key_id or max(self.keys.keys())
            }
            
        except Exception as e:
            self.logger.error(f"Encryption failed: {str(e)}")
            raise
            
    async def decrypt(self,
                     encrypted_data: Dict[str, str]) -> bytes:
        """Decrypt data with specified key."""
        try:
            # Get key
            key_id = encrypted_data["key_id"]
            key = self.keys[key_id]
            fernet = Fernet(key)
            
            # Decode and decrypt data
            data = base64.urlsafe_b64decode(encrypted_data["data"])
            
            return fernet.decrypt(data)
            
        except Exception as e:
            self.logger.error(f"Decryption failed: {str(e)}")
            raise
            
    async def encrypt_file(self,
                          file_path: Path,
                          output_path: Optional[Path] = None) -> Dict[str, str]:
        """Encrypt file with current key."""
        try:
            if not output_path:
                output_path = file_path.with_suffix(file_path.suffix + '.enc')
                
            async with aiofiles.open(file_path, 'rb') as f:
                data = await f.read()
                
            # Encrypt data
            encrypted = await self.encrypt(data)
            
            # Save encrypted file
            async with aiofiles.open(output_path, 'w') as f:
                await f.write(json.dumps(encrypted))
                
            return {
                "path": str(output_path),
                "key_id": encrypted["key_id"]
            }
            
        except Exception as e:
            self.logger.error(f"File encryption failed: {str(e)}")
            raise
            
    async def decrypt_file(self,
                          file_path: Path,
                          output_path: Optional[Path] = None) -> Path:
        """Decrypt encrypted file."""
        try:
            if not output_path:
                output_path = file_path.with_suffix('')
                
            # Read encrypted data
            async with aiofiles.open(file_path, 'r') as f:
                encrypted = json.loads(await f.read())
                
            # Decrypt data
            decrypted = await self.decrypt(encrypted)
            
            # Save decrypted file
            async with aiofiles.open(output_path, 'wb') as f:
                await f.write(decrypted)
                
            return output_path
            
        except Exception as e:
            self.logger.error(f"File decryption failed: {str(e)}")
            raise
            
    async def cleanup(self):
        """Cleanup resources."""
        pass  # No cleanup needed for encryption service

# Global encryption service instance
encryption_service = EncryptionService() 