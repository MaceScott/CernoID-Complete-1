"""
Enhanced configuration management with validation and environment handling.
"""
from typing import Dict, Any, Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import HttpUrl, SecretStr, field_validator, Field, validator
import json
import os
import logging
from enum import Enum
from functools import lru_cache

# Configure module logger
logger = logging.getLogger(__name__)

class Environment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"

class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    environment: str = Field(default="development")
    debug: bool = Field(default=True)
    log_level: str = Field(default="INFO")
    
    # Database
    db_host: str = Field(default="db")
    db_port: int = Field(default=5432)
    db_user: str = Field(default="postgres")
    db_password: str = Field(default="postgres")
    db_name: str = Field(default="cernoid")
    database_url: str = Field(default="postgresql+asyncpg://postgres:postgres@db:5432/cernoid")
    
    # Database Pool
    db_pool_size: int = Field(default=5)
    db_max_overflow: int = Field(default=10)
    db_pool_timeout: int = Field(default=30)
    sql_debug: bool = Field(default=False)
    
    # Redis
    redis_host: str = Field(default="redis")
    redis_port: int = Field(default=6379)
    
    # Security
    secret_key: str = Field(default="your-secret-key-here")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    
    # CORS
    allowed_origins: List[str] = Field(default=["*"])
    
    # Face Recognition
    face_recognition_model: str = Field(default="hog")
    min_face_confidence: float = Field(default=0.6)
    face_encoding_batch_size: int = Field(default=32)
    face_detection_cascade_path: str = Field(default="models/haarcascade_frontalface_default.xml")
    face_detection_torch_model_path: str = Field(default="models/face_detection.pt")
    face_encoding_dlib_model_path: str = Field(default="models/dlib_face_recognition_resnet_model_v1.dat")
    face_encoding_torch_model_path: str = Field(default="models/face_encoding.pt")
    recognition_landmark_model: str = Field(default="models/face_landmarks.pt")
    recognition_attribute_model: str = Field(default="models/face_attributes.pt")
    recognition_face_size: int = Field(default=160)
    recognition_min_quality: float = Field(default=0.5)
    recognition_focal_length: float = Field(default=615.0)
    recognition_avg_face_width: float = Field(default=0.15)
    recognition_activation_range: float = Field(default=1.5)
    recognition_long_range_threshold: float = Field(default=6.0)
    face_recognition_cache_size: int = Field(default=10000)
    face_recognition_cache_ttl: int = Field(default=3600)
    face_recognition_matching_threshold: float = Field(default=0.6)
    face_recognition_min_face_size: tuple[int, int] = Field(default=(30, 30))
    face_recognition_scale_factor: float = Field(default=1.1)
    gpu_enabled: bool = Field(default=True)
    face_detection_min_confidence: float = Field(default=0.8)
    tts_responses_path: str = Field(default="config/tts_responses.json")
    
    @validator("database_url", pre=True)
    def validate_database_url(cls, v: str, values: dict) -> str:
        """Validate and construct database URL if not provided."""
        if not v:
            return (
                f"postgresql+asyncpg://{values['db_user']}:{values['db_password']}"
                f"@{values['db_host']}:{values['db_port']}/{values['db_name']}"
            )
        return v
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    try:
        settings = Settings()
        logger.info(f"Loaded settings for environment: {settings.environment}")
        return settings
    except Exception as e:
        logger.error(f"Failed to load settings: {str(e)}")
        raise

alert_preferences: Dict[str, Any] = {
    'enabled': True,
    'channels': ['EMAIL'],
    'minSeverity': 'MEDIUM',
    'quietHours': {
        'enabled': False,
        'start': '22:00',
        'end': '07:00'
    },
    'thresholds': {
        'cpu': 80,
        'memory': 80,
        'disk': 90,
        'network': 1000
    }
}

smtp_config: Dict[str, Any] = {
    'host': 'smtp.gmail.com',
    'port': 587,
    'username': '',
    'password': '',
    'from_email': '',
    'to_email': '',
    'use_tls': True
}

# Create global settings instance
settings = Settings()

__all__ = ['Settings', 'settings']
