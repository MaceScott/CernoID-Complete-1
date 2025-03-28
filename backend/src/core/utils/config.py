from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    """Base configuration class."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"  # Allow extra fields from env vars
    )
    
    # Database settings
    DB_HOST: str = "db"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_NAME: str = "cernoid"
    
    # Redis settings
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    
    # JWT settings
    JWT_SECRET: str = "your-secret-key"
    
    # Environment settings
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # CORS settings
    CORS_ORIGIN: str = "http://localhost:3000"
    
    # Face recognition settings
    FACE_RECOGNITION_MODEL_PATH: str = "/app/models/face_recognition"
    FACE_DETECTION_CONFIDENCE: float = 0.85

@lru_cache()
def get_settings() -> Config:
    """
    Get application settings.
    
    Returns:
        Config: Application settings instance.
    """
    return Config() 