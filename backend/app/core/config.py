from pydantic_settings import BaseSettings
from typing import Optional, List
from functools import lru_cache
import os
from pathlib import Path

class Settings(BaseSettings):
    # Core Settings
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    PORT: int = 8000
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    BACKEND_WORKERS: int = 4

    # Database
    DATABASE_URL: str
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    ALEMBIC_CONFIG: str = "alembic.ini"
    MIGRATION_DIR: str = "migrations"
    TEST_DATABASE_URL: Optional[str] = None

    # Redis
    REDIS_URL: str
    REDIS_HOST: str
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str
    TEST_REDIS_URL: Optional[str] = None

    # Security
    JWT_SECRET: str
    JWT_EXPIRES_IN: str = "24h"
    JWT_REFRESH_EXPIRES_IN: str = "7d"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080
    CORS_ORIGIN: str
    ALLOWED_ORIGINS: str = "*"
    RATE_LIMIT_WINDOW: int = 15
    RATE_LIMIT_MAX_REQUESTS: int = 100
    SECRET_KEY: str
    SSL_ENABLED: bool = True
    SSL_VERIFY: bool = True
    SSL_CERT_PATH: Optional[str] = None
    SSL_KEY_PATH: Optional[str] = None

    # Face Recognition
    ENABLE_FACE_RECOGNITION: bool = False
    FACE_RECOGNITION_MODEL: str = "hog"
    FACE_RECOGNITION_MODEL_PATH: str
    FACE_DETECTION_CONFIDENCE: float = 0.6
    FACE_DETECTION_CASCADE_PATH: str
    FACE_DETECTION_TORCH_MODEL_PATH: str
    FACE_DETECTION_SCALE_FACTOR: float = 1.1
    FACE_DETECTION_MIN_NEIGHBORS: int = 5
    FACE_DETECTION_MIN_WIDTH: int = 30
    FACE_DETECTION_MIN_HEIGHT: int = 30

    # Face Encoding
    FACE_ENCODING_BATCH_SIZE: int = 32
    FACE_ENCODING_TOLERANCE: float = 0.6
    FACE_ENCODING_DLIB_MODEL_PATH: str
    FACE_ENCODING_TORCH_MODEL_PATH: str

    # Recognition Models
    RECOGNITION_LANDMARK_MODEL: str
    RECOGNITION_ATTRIBUTE_MODEL: str
    RECOGNITION_FOCAL_LENGTH: float = 500.0
    RECOGNITION_AVG_FACE_WIDTH: float = 0.15
    RECOGNITION_ACTIVATION_RANGE: float = 2.0
    RECOGNITION_LONG_RANGE_THRESHOLD: float = 5.0
    RECOGNITION_FACE_SIZE: int = 224
    RECOGNITION_MIN_QUALITY: float = 0.5

    # GPU and Performance
    GPU_ENABLED: bool = False
    FACE_RECOGNITION_CACHE_SIZE: int = 1000
    FACE_RECOGNITION_CACHE_TTL: int = 3600
    FACE_RECOGNITION_MIN_FACE_SIZE: int = 20
    FACE_RECOGNITION_SCALE_FACTOR: float = 1.1
    FACE_RECOGNITION_MATCHING_THRESHOLD: float = 0.6

    # Monitoring
    ENABLE_METRICS: bool = True
    ENABLE_TRACING: bool = True
    PROMETHEUS_MULTIPROC_DIR: str = "/tmp"
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    BACKEND_LOG_LEVEL: str = "INFO"
    GRAFANA_ADMIN_PASSWORD: str

    # Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = None

    # Feature Flags
    ENABLE_ANALYTICS: bool = False
    ENABLE_LOGGING: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True

    def validate(self):
        """Validate environment variables and file paths"""
        # Validate required files exist
        required_files = [
            self.FACE_DETECTION_CASCADE_PATH,
            self.FACE_DETECTION_TORCH_MODEL_PATH,
            self.FACE_ENCODING_DLIB_MODEL_PATH,
            self.FACE_ENCODING_TORCH_MODEL_PATH,
            self.RECOGNITION_LANDMARK_MODEL,
            self.RECOGNITION_ATTRIBUTE_MODEL,
        ]
        
        for file_path in required_files:
            if not Path(file_path).exists():
                raise ValueError(f"Required file not found: {file_path}")

        # Validate numeric ranges
        if not 0 <= self.FACE_DETECTION_CONFIDENCE <= 1:
            raise ValueError("FACE_DETECTION_CONFIDENCE must be between 0 and 1")
        
        if not 0 <= self.FACE_ENCODING_TOLERANCE <= 1:
            raise ValueError("FACE_ENCODING_TOLERANCE must be between 0 and 1")
        
        if not 0 <= self.RECOGNITION_MIN_QUALITY <= 1:
            raise ValueError("RECOGNITION_MIN_QUALITY must be between 0 and 1")

        # Validate SSL configuration
        if self.SSL_ENABLED:
            if not self.SSL_CERT_PATH or not self.SSL_KEY_PATH:
                raise ValueError("SSL_CERT_PATH and SSL_KEY_PATH are required when SSL_ENABLED is true")
            if not Path(self.SSL_CERT_PATH).exists():
                raise ValueError(f"SSL certificate not found: {self.SSL_CERT_PATH}")
            if not Path(self.SSL_KEY_PATH).exists():
                raise ValueError(f"SSL key not found: {self.SSL_KEY_PATH}")

        # Validate email configuration
        if any([self.SMTP_HOST, self.SMTP_PORT, self.SMTP_USER, self.SMTP_PASSWORD, self.SMTP_FROM]):
            if not all([self.SMTP_HOST, self.SMTP_PORT, self.SMTP_USER, self.SMTP_PASSWORD, self.SMTP_FROM]):
                raise ValueError("All SMTP settings must be provided if any are set")

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    settings = Settings()
    settings.validate()
    return settings

settings = get_settings() 