"""
Enhanced configuration management with validation and environment handling.
"""
from typing import Dict, Any, Optional
from pydantic import BaseSettings, validator
import json
import os

class Environment(str):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class Settings(BaseSettings):
    """Enhanced settings with validation"""
    
    # Environment
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    
    # Feature flags
    features: Dict[str, bool] = {}
    
    @validator("features", pre=True)
    def parse_features(cls, v: Any) -> Dict[str, bool]:
        if isinstance(v, str):
            return json.loads(v)
        return v
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if feature is enabled"""
        return self.features.get(feature, False)
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == Environment.PRODUCTION

    # API Settings
    api_version: str = "v1"
    api_prefix: str = f"/api/{api_version}"

    # Security
    jwt_secret_key: str
    token_expire_minutes: int = 30
    allowed_hosts: List[str] = ["*"]
    cors_origins: List[str] = ["*"]

    # Face Recognition
    face_detection_confidence: float = 0.8
    face_recognition_threshold: float = 0.6
    model_path: str = "models/recognition_model.dat"

    # Database
    database_url: str
    max_connections: int = 10

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings() # Alert Settings
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
