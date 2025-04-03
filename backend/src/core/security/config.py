from typing import List, Optional
from pydantic import BaseSettings, validator
from ..logging.config import LogConfig

logger = LogConfig().get_logger(__name__)

class SecuritySettings(BaseSettings):
    """
    Security settings configuration.
    """
    # Session settings
    SESSION_LIFETIME: int = 3600  # 1 hour
    MAX_SESSIONS_PER_USER: int = 5
    SESSION_CLEANUP_INTERVAL: int = 300  # 5 minutes
    
    # CSRF settings
    CSRF_TOKEN_LIFETIME: int = 3600  # 1 hour
    CSRF_CLEANUP_INTERVAL: int = 300  # 5 minutes
    
    # Rate limiting settings
    RATE_LIMIT_MAX_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_BLOCK_DURATION: int = 300  # 5 minutes
    
    # Password settings
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    
    # Security headers
    ENABLE_HSTS: bool = True
    HSTS_MAX_AGE: int = 31536000  # 1 year
    HSTS_INCLUDE_SUBDOMAINS: bool = True
    ENABLE_XSS_PROTECTION: bool = True
    ENABLE_CONTENT_TYPE_NOSNIFF: bool = True
    ENABLE_FRAME_DENY: bool = True
    
    # Content Security Policy
    CSP_ENABLED: bool = True
    CSP_DEFAULT_SRC: List[str] = ["'self'"]
    CSP_SCRIPT_SRC: List[str] = ["'self'", "'unsafe-inline'", "'unsafe-eval'"]
    CSP_STYLE_SRC: List[str] = ["'self'", "'unsafe-inline'"]
    CSP_IMG_SRC: List[str] = ["'self'", "data:", "https:"]
    CSP_FONT_SRC: List[str] = ["'self'", "data:"]
    CSP_CONNECT_SRC: List[str] = ["'self'", "https:"]
    
    # Cookie settings
    COOKIE_SECURE: bool = True
    COOKIE_HTTPONLY: bool = True
    COOKIE_SAMESITE: str = "Strict"
    
    # Excluded paths from security checks
    EXCLUDED_PATHS: List[str] = [
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/metrics"
    ]
    
    # Allowed domains for CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # JWT settings
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    @validator("JWT_SECRET_KEY")
    def validate_jwt_secret_key(cls, v):
        if not v or len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long")
        return v
        
    @validator("ALLOWED_ORIGINS")
    def validate_allowed_origins(cls, v):
        if not v:
            raise ValueError("ALLOWED_ORIGINS cannot be empty")
        return v
        
    @validator("EXCLUDED_PATHS")
    def validate_excluded_paths(cls, v):
        if not v:
            raise ValueError("EXCLUDED_PATHS cannot be empty")
        return v
        
    class Config:
        env_prefix = "SECURITY_"
        case_sensitive = True

# Global security settings instance
security_settings = SecuritySettings() 