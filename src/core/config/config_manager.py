from typing import Any, Dict, Optional
import yaml
import os
from pathlib import Path
from core.error_handling import handle_exceptions

class ConfigManager:
    def __init__(self):
        self.config: Dict = {}
        self.env = os.getenv('CERNOID_ENV', 'development')
        self.load_config()

    @handle_exceptions(logger=config_logger.error)
    def load_config(self):
        config_path = Path(f"config/{self.env}.yaml")
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        # Override with environment variables
        self._override_from_env()

    def _override_from_env(self):
        for key in os.environ:
            if key.startswith('CERNOID_'):
                config_key = key[8:].lower()
                self._set_nested_config(config_key, os.environ[key])

    def get(self, key: str, default: Any = None) -> Any:
        try:
            value = self.config
            for k in key.split('.'):
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default 
