"""Configuration management module."""
from typing import Any, Dict, Optional, Union
from pathlib import Path
import logging
from pydantic import BaseModel
import yaml

logger = logging.getLogger(__name__)

class ConfigSection(BaseModel):
    """Configuration section with validation"""
    database: Dict[str, Any]
    recognition: Dict[str, Any]
    camera: Dict[str, Any]
    logging: Dict[str, Any]
    security: Dict[str, Any]

class ConfigManager:
    """System configuration manager"""
    
    def __init__(self, config_path: Union[str, Path]):
        self._config_path = Path(config_path)
        self._config: Dict = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from file"""
        try:
            if self._config_path.exists():
                with open(self._config_path, 'r') as f:
                    self._config = yaml.safe_load(f)
            else:
                logger.warning(f"Config file {self._config_path} not found, using defaults")
                self._config = {}
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self._config = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        try:
            value = self._config
            for k in key.split('.'):
                value = value.get(k, default)
                if value is None:
                    return default
            return value
        except Exception:
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        try:
            keys = key.split('.')
            config = self._config
            
            # Navigate to the correct nested level
            for k in keys[:-1]:
                config = config.setdefault(k, {})
            
            # Set the value
            config[keys[-1]] = value
            
        except Exception as e:
            logger.error(f"Failed to set config value: {e}")
            raise ValueError(f"Failed to set configuration value: {e}")
    
    def save(self) -> None:
        """Save configuration to file"""
        try:
            # Create parent directories if needed
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save config
            with open(self._config_path, 'w') as f:
                yaml.safe_dump(self._config, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise IOError(f"Failed to save configuration: {e}")

# Initialize global config instance
config = ConfigManager("config/config.yaml") 