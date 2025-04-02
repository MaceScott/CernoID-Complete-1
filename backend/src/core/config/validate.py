from typing import Dict, Optional
from pydantic import BaseSettings, validator, HttpUrl, PostgresDsn, RedisDsn
import os

class Settings(BaseSettings):
    # Core Settings
    ENVIRONMENT: str
    DEBUG: bool
    BACKEND_HOST: str
    BACKEND_PORT: int
    BACKEND_WORKERS: int

    # Database
    DATABASE_URL: PostgresDsn
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    ALEMBIC_CONFIG: str = "alembic.ini"
    MIGRATION_DIR: str = "migrations"
    TEST_DATABASE_URL: Optional[PostgresDsn] = None

    # Redis
    REDIS_URL: RedisDsn
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    TEST_REDIS_URL: Optional[RedisDsn] = None

    # JWT Authentication
    JWT_SECRET: str
    JWT_EXPIRES_IN: str
    JWT_REFRESH_EXPIRES_IN: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_MINUTES: int

    # Security
    CORS_ORIGIN: HttpUrl
    ALLOWED_ORIGINS: str
    RATE_LIMIT_WINDOW: int
    RATE_LIMIT_MAX_REQUESTS: int
    SECRET_KEY: str

    # Face Recognition
    ENABLE_FACE_RECOGNITION: bool
    FACE_RECOGNITION_MODEL: str
    FACE_RECOGNITION_MODEL_PATH: str
    FACE_DETECTION_CONFIDENCE: float
    FACE_DETECTION_CASCADE_PATH: str
    FACE_DETECTION_TORCH_MODEL_PATH: str
    FACE_DETECTION_SCALE_FACTOR: float
    FACE_DETECTION_MIN_NEIGHBORS: int
    FACE_DETECTION_MIN_WIDTH: int
    FACE_DETECTION_MIN_HEIGHT: int

    # Face Encoding
    FACE_ENCODING_BATCH_SIZE: int
    FACE_ENCODING_TOLERANCE: float
    FACE_ENCODING_DLIB_MODEL_PATH: str
    FACE_ENCODING_TORCH_MODEL_PATH: str

    # Recognition Models
    RECOGNITION_LANDMARK_MODEL: str
    RECOGNITION_ATTRIBUTE_MODEL: str
    RECOGNITION_FOCAL_LENGTH: float
    RECOGNITION_AVG_FACE_WIDTH: float
    RECOGNITION_ACTIVATION_RANGE: float
    RECOGNITION_LONG_RANGE_THRESHOLD: float
    RECOGNITION_FACE_SIZE: int
    RECOGNITION_MIN_QUALITY: float

    # GPU and Performance
    GPU_ENABLED: bool
    FACE_RECOGNITION_CACHE_SIZE: int
    FACE_RECOGNITION_CACHE_TTL: int
    FACE_RECOGNITION_MIN_FACE_SIZE: int
    FACE_RECOGNITION_SCALE_FACTOR: float
    FACE_RECOGNITION_MATCHING_THRESHOLD: float

    # Monitoring
    ENABLE_METRICS: bool
    ENABLE_TRACING: bool
    PROMETHEUS_MULTIPROC_DIR: str
    LOG_LEVEL: str
    LOG_FORMAT: str
    BACKEND_LOG_LEVEL: str
    GRAFANA_ADMIN_PASSWORD: str

    # Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = None

    # Feature Flags
    ENABLE_ANALYTICS: bool
    ENABLE_LOGGING: bool

    # Vault Configuration
    VAULT_ADDR: Optional[HttpUrl] = None
    VAULT_TOKEN: Optional[str] = None
    VAULT_PATH: Optional[str] = None

    @validator("FACE_DETECTION_CONFIDENCE")
    def validate_confidence(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        return v

    @validator("FACE_DETECTION_SCALE_FACTOR")
    def validate_scale_factor(cls, v):
        if v <= 1:
            raise ValueError("Scale factor must be greater than 1")
        return v

    @validator("FACE_DETECTION_MIN_NEIGHBORS")
    def validate_min_neighbors(cls, v):
        if v < 0:
            raise ValueError("Minimum neighbors cannot be negative")
        return v

    @validator("FACE_DETECTION_MIN_WIDTH", "FACE_DETECTION_MIN_HEIGHT")
    def validate_min_dimensions(cls, v):
        if v < 1:
            raise ValueError("Minimum dimensions must be positive")
        return v

    @validator("FACE_ENCODING_TOLERANCE")
    def validate_tolerance(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("Tolerance must be between 0 and 1")
        return v

    @validator("RECOGNITION_MIN_QUALITY")
    def validate_quality(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("Quality must be between 0 and 1")
        return v

    @validator("FACE_RECOGNITION_MATCHING_THRESHOLD")
    def validate_threshold(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("Threshold must be between 0 and 1")
        return v

    @validator("RATE_LIMIT_WINDOW", "RATE_LIMIT_MAX_REQUESTS")
    def validate_rate_limit(cls, v):
        if v <= 0:
            raise ValueError("Rate limit values must be positive")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True

def validate_env() -> Dict:
    """
    Validate environment variables and return settings.
    
    Returns:
        Dict containing validated settings or error information.
    """
    try:
        settings = Settings()
        return {"success": True, "settings": settings}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Export validated settings
settings = validate_env()["settings"] if validate_env()["success"] else None 