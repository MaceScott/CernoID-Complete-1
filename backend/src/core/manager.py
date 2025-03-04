import yaml
from pathlib import Path
from typing import Any, Dict
from ..error_handling import handle_exceptions

class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.config_path = Path('config/config.yaml')
            self.config: Dict[str, Any] = {}
            self.load_config()
            self.initialized = True

    @handle_exceptions(logger=config_logger.error)
    def load_config(self):
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    @handle_exceptions(logger=config_logger.error)
    def save_config(self):
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f) 
