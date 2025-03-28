"""
Enhanced configuration management with validation and environment handling.
"""
from typing import Dict, Any, Optional, List, Union, Tuple
from pydantic import BaseModel, Field, field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
import json
import os
import logging
from enum import Enum
from functools import lru_cache
import ast
from pathlib import Path

# Configure module logger
logger = logging.getLogger(__name__)

class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"  # Allow extra fields from env vars
    )

    # Core settings
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    TESTING: bool = False  # Flag for test environment
    
    # Application settings
    APP_NAME: str = "CernoID"
    APP_DESCRIPTION: str = "Advanced Face Recognition System"
    APP_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "CernoID API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Advanced Face Recognition System"

    # Feature flags
    ENABLE_FACE_RECOGNITION: bool = True
    ENABLE_SYSTEM_MONITORING: bool = True
    USE_GPU: bool = False
    MODEL_PATH: str = "models"

    # Database settings
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/cernoid"
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800

    # Redis settings
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = "redis_password"

    @computed_field
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Security settings
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # CORS settings
    ALLOWED_ORIGINS: str = "*"

    @property
    def allowed_origins_list(self) -> List[str]:
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    # Face recognition settings
    FACE_RECOGNITION_MODEL: str = "face_recognition_model"
    MIN_FACE_CONFIDENCE: float = 0.6
    FACE_ENCODING_BATCH_SIZE: int = 32
    FACE_RECOGNITION_TOLERANCE: float = 0.6
    
    # Face detection settings
    FACE_DETECTION_CASCADE_PATH: str = "/app/models/haarcascade_frontalface_default.xml"
    FACE_DETECTION_TORCH_MODEL_PATH: str = "/app/models/face_detection.pt"
    FACE_DETECTION_SCALE_FACTOR: float = 1.1
    FACE_DETECTION_MIN_NEIGHBORS: int = 5
    FACE_DETECTION_MIN_WIDTH: int = 30
    FACE_DETECTION_MIN_HEIGHT: int = 30

    @property
    def FACE_DETECTION_MIN_SIZE(self) -> Tuple[int, int]:
        return (self.FACE_DETECTION_MIN_WIDTH, self.FACE_DETECTION_MIN_HEIGHT)
    
    # Face encoding settings
    FACE_ENCODING_DLIB_MODEL_PATH: str = "/app/models/dlib_face_recognition_resnet_model_v1.dat"
    FACE_ENCODING_TORCH_MODEL_PATH: str = "/app/models/face_encoding.pt"
    
    # Landmark and attribute models
    RECOGNITION_LANDMARK_MODEL: str = "/app/models/face_landmarks.pt"
    RECOGNITION_ATTRIBUTE_MODEL: str = "/app/models/face_attributes.pt"
    
    # GPU settings
    GPU_ENABLED: bool = False
    FACE_RECOGNITION_CACHE_SIZE: int = 1000
    FACE_RECOGNITION_CACHE_TTL: int = 3600  # 1 hour
    RECOGNITION_FACE_SIZE: int = 224
    RECOGNITION_MIN_QUALITY: float = 0.5
    FACE_RECOGNITION_MIN_FACE_SIZE: int = 20
    FACE_RECOGNITION_SCALE_FACTOR: float = 1.1
    FACE_RECOGNITION_MATCHING_THRESHOLD: float = 0.6
    
    # Recognition settings
    RECOGNITION_FOCAL_LENGTH: float = 500.0
    RECOGNITION_AVG_FACE_WIDTH: float = 0.15  # meters
    RECOGNITION_ACTIVATION_RANGE: float = 2.0  # meters
    RECOGNITION_LONG_RANGE_THRESHOLD: float = 5.0  # meters

    # Test mode flag
    TESTING: bool = False
    
    # Model paths and configurations
    GPU_DEVICE: str = "cuda:0"
    FACE_DETECTION_MODEL: str = "face_detection_model"

class TestSettings(Settings):
    """Test settings."""
    DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"
    DEBUG: bool = True
    TESTING: bool = True
    DB_ECHO: bool = True
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    ENABLE_FACE_RECOGNITION: bool = False
    USE_GPU: bool = False
    MODEL_PATH: str = "test_models"
    API_V1_STR: str = "/api/v1"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Advanced Face Recognition System"

@lru_cache
def get_settings() -> Settings:
    """Get settings instance with environment variables."""
    if os.getenv("TESTING"):
        return TestSettings()
    return Settings()

__all__ = ['Settings', 'get_settings', 'Environment']
