from typing import Optional
import os
from pathlib import Path
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SecretsManager:
    def __init__(self, key_file: Optional[str] = None):
        # Use a more secure default path
        self.key_file = key_file or os.getenv('SECRETS_KEY_FILE', '/etc/cernoid/secrets/.secrets.key')
        self._key = self._load_or_generate_key()
        self._fernet = Fernet(self._key)
        self._key_rotation_date = self._get_key_rotation_date()

    def _get_key_rotation_date(self) -> datetime:
        """Get the key rotation date from metadata or default to creation date"""
        metadata_file = Path(f"{self.key_file}.meta")
        if metadata_file.exists():
            try:
                metadata = json.loads(metadata_file.read_text())
                return datetime.fromisoformat(metadata.get('rotation_date'))
            except (json.JSONDecodeError, ValueError):
                logger.warning("Invalid metadata file, using default rotation date")
        return datetime.now()

    def _should_rotate_key(self) -> bool:
        """Check if key should be rotated (every 90 days)"""
        return datetime.now() - self._key_rotation_date > timedelta(days=90)

    def _rotate_key(self) -> None:
        """Rotate the encryption key"""
        old_key = self._key
        new_key = Fernet.generate_key()
        
        # Backup old key
        backup_file = Path(f"{self.key_file}.{datetime.now().strftime('%Y%m%d')}")
        backup_file.write_bytes(old_key)
        
        # Update key and metadata
        Path(self.key_file).write_bytes(new_key)
        self._key = new_key
        self._fernet = Fernet(new_key)
        self._key_rotation_date = datetime.now()
        
        # Update metadata
        metadata = {
            'rotation_date': self._key_rotation_date.isoformat(),
            'backup_files': [str(backup_file)]
        }
        Path(f"{self.key_file}.meta").write_text(json.dumps(metadata))

    def _load_or_generate_key(self) -> bytes:
        """Load existing key or generate a new one"""
        key_path = Path(self.key_file)
        if key_path.exists():
            if self._should_rotate_key():
                self._rotate_key()
            return key_path.read_bytes()
        
        # Generate a new key
        key = Fernet.generate_key()
        key_path.parent.mkdir(parents=True, exist_ok=True)
        key_path.write_bytes(key)
        return key

    def _derive_key(self, password: str, salt: Optional[bytes] = None) -> bytes:
        """Derive a key from a password using PBKDF2"""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def encrypt(self, data: str) -> str:
        """Encrypt a string"""
        return self._fernet.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt a string"""
        return self._fernet.decrypt(encrypted_data.encode()).decode()

    def encrypt_file(self, file_path: str) -> None:
        """Encrypt a file"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        data = path.read_text()
        encrypted_data = self.encrypt(data)
        path.write_text(encrypted_data)

    def decrypt_file(self, file_path: str) -> None:
        """Decrypt a file"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        encrypted_data = path.read_text()
        decrypted_data = self.decrypt(encrypted_data)
        path.write_text(decrypted_data)

    def get_secret(self, key: str) -> str:
        """Get a secret value"""
        encrypted_value = os.getenv(key)
        if not encrypted_value:
            raise ValueError(f"Secret not found: {key}")
        return self.decrypt(encrypted_value)

    def set_secret(self, key: str, value: str) -> None:
        """Set a secret value"""
        encrypted_value = self.encrypt(value)
        os.environ[key] = encrypted_value

    def load_secrets_file(self, file_path: str) -> None:
        """Load secrets from a JSON file"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Secrets file not found: {file_path}")
        
        secrets = json.loads(path.read_text())
        for key, value in secrets.items():
            self.set_secret(key, value)

    def save_secrets_file(self, file_path: str) -> None:
        """Save secrets to a JSON file"""
        secrets = {}
        for key, value in os.environ.items():
            if key.startswith('SECRET_'):
                secrets[key] = self.get_secret(key)
        
        path = Path(file_path)
        path.write_text(json.dumps(secrets, indent=2))

# Create a global instance
secrets_manager = SecretsManager() 