from typing import Dict, Any
from pydantic import BaseSettings

class BaseSettings(BaseSettings):
    class Config:
        env_file = '.env'
        case_sensitive = False
