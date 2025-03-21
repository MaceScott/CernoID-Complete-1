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
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Database settings
    DB_HOST: str = "db"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_NAME: str = "cernoid"

    @computed_field
    def DATABASE_URL(self) -> str:
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Redis settings
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

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
    FACE_RECOGNITION_MODEL: str = "hog"
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

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    try:
        settings = Settings()
        logger.info(f"Loaded settings for environment: {settings.ENVIRONMENT}")
        return settings
    except Exception as e:
        logger.error(f"Failed to load settings: {str(e)}")
        raise

# Create global settings instance
settings = get_settings()

__all__ = ['Settings', 'settings', 'Environment']
