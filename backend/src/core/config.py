from typing import Any, Dict, Optional
import os
from dotenv import load_dotenv
from core.logging import get_logger

logger = get_logger(__name__)

class ConfigManager:
    """Manages application configuration with environment variable support."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._load_env_vars()
        
    def _load_env_vars(self) -> None:
        """Load environment variables from .env file."""
        try:
            load_dotenv()
        except Exception as e:
            logger.warning(f"Failed to load .env file: {e}")
            
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with environment variable fallback."""
        # First try environment variable
        env_value = os.getenv(key)
        if env_value is not None:
            return env_value
            
        # Then try config dictionary
        return self.config.get(key, default)
        
    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer configuration value."""
        value = self.get(key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
            
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean configuration value."""
        value = self.get(key, default)
        if isinstance(value, bool):
            return value
        return str(value).lower() in ('true', '1', 'yes')
        
    def get_list(self, key: str, default: Optional[list] = None) -> list:
        """Get list configuration value."""
        value = self.get(key, default)
        if value is None:
            return default or []
        if isinstance(value, list):
            return value
        return [item.strip() for item in str(value).split(',')]
        
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self.config[key] = value
        
    def update(self, config: Dict[str, Any]) -> None:
        """Update configuration with new values."""
        self.config.update(config)
        
    def to_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary."""
        return self.config.copy()

# Default configuration
default_config = {
    'APP_NAME': 'CernoID',
    'APP_ENV': 'development',
    'DEBUG': True,
    'API_VERSION': '1.0.0',
    'HOST': '0.0.0.0',
    'PORT': 8000,
    'WORKERS': 4,
    'LOG_LEVEL': 'INFO',
    'DATABASE_URL': 'postgresql://postgres:postgres@db:5432/cernoid',
    'REDIS_URL': 'redis://redis:6379/0',
    'JWT_SECRET': 'your-secret-key',
    'JWT_ALGORITHM': 'HS256',
    'ACCESS_TOKEN_EXPIRE_MINUTES': 30,
    'FACE_RECOGNITION_MODEL': 'models/face_recognition_model.pkl',
    'GPU_ENABLED': False,
    'MAX_WORKERS': 4,
    'BATCH_SIZE': 32,
    'CACHE_TTL': 3600,
    'ALLOWED_ORIGINS': ['*'],
    'CORS_ENABLED': True,
    'RATE_LIMIT_ENABLED': True,
    'RATE_LIMIT_REQUESTS': 100,
    'RATE_LIMIT_PERIOD': 60,
    'HEALTH_CHECK_INTERVAL': 30,
    'HEALTH_CHECK_TIMEOUT': 5,
    'HEALTH_CHECK_RETRIES': 3
}

# Global configuration instance
config = ConfigManager(default_config) 