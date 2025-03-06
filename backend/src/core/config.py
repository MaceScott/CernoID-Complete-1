"""Application configuration."""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator

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

# Create global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get application settings."""
    return settings 