from typing import Any, Dict, Optional, List, Union
import yaml
from pathlib import Path
import os
from datetime import datetime
import logging
import json
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from ..utils.errors import ConfigurationError, handle_errors, ConfigError
from .validator import ConfigValidator
from ..base import BaseComponent
import hashlib
from copy import deepcopy
import jsonschema

logger = logging.getLogger(__name__)

@dataclass
class ConfigSection:
    """Configuration section with validation"""
    database: Dict[str, Any]
    recognition: Dict[str, Any]
    camera: Dict[str, Any]
    logging: Dict[str, Any]
    security: Dict[str, Any]

@dataclass
class ConfigurationSource:
    """Configuration source definition"""
    type: str
    path: Optional[Path] = None
    env_prefix: Optional[str] = None
    required: bool = True
    default: Optional[Dict] = None

class ConfigManager(BaseComponent):
    """System configuration manager"""
    
    def __init__(self, config_path: Union[str, Path]):
        self._config_path = Path(config_path)
        self._config: Dict = {}
        self._schema: Dict = {}
        self._defaults: Dict = {}
        self._watchers: Dict[str, callable] = {}
        
        # Load schema and defaults
        self._load_schema()
        self._load_defaults()
        
        # Initialize base component with loaded config
        super().__init__(self._load_config())
        
        # Track changes
        self._last_modified = self._config_path.stat().st_mtime
        self._pending_changes: Dict = {}

    def _load_schema(self) -> None:
        """Load configuration schema"""
        try:
            schema_path = Path(__file__).parent / 'schema.yaml'
            with open(schema_path, 'r') as f:
                self._schema = yaml.safe_load(f)
        except Exception as e:
            raise ConfigError(f"Failed to load schema: {str(e)}")

    def _load_defaults(self) -> None:
        """Load default configuration"""
        self._defaults = {
            'system': {
                'log_level': 'INFO',
                'log_file': 'logs/system.log',
                'debug': False
            },
            'recognition': {
                'threshold': 0.6,
                'min_face_size': 64,
                'anti_spoofing': True,
                'model': 'dlib_resnet'
            },
            'camera': {
                'frame_rate': 30,
                'resolution': '1280x720',
                'buffer_size': 100
            },
            'alerts': {
                'min_level': 'medium',
                'buffer_size': 1000,
                'retention_days': 30
            },
            'api': {
                'host': '0.0.0.0',
                'port': 8000,
                'workers': 4,
                'rate_limit': 100
            },
            'websocket': {
                'max_connections': 100,
                'ping_interval': 30
            },
            'database': {
                'url': 'mongodb://localhost:27017',
                'name': 'cernoid',
                'pool_size': 10
            },
            'security': {
                'session_timeout': 3600,
                'token_expiry': 86400,
                'min_password_length': 8
            }
        }

    def _load_config(self) -> Dict:
        """Load configuration from file"""
        try:
            if self._config_path.exists():
                with open(self._config_path, 'r') as f:
                    if self._config_path.suffix == '.json':
                        config = json.load(f)
                    else:
                        config = yaml.safe_load(f)
                
                # Merge with defaults
                self._config = self._merge_configs(self._defaults, config)
                
                # Validate configuration
                self._validate_config(self._config)
                
                return self._config
            else:
                # Use defaults if no config file exists
                self._config = self._defaults.copy()
                return self._config
                
        except Exception as e:
            raise ConfigError(f"Failed to load config: {str(e)}")

    def _merge_configs(self, base: Dict, override: Dict) -> Dict:
        """Recursively merge configuration dictionaries"""
        merged = base.copy()
        
        for key, value in override.items():
            if (key in merged and isinstance(merged[key], dict) 
                and isinstance(value, dict)):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
                
        return merged

    def _validate_config(self, config: Dict) -> None:
        """Validate configuration against schema"""
        try:
            jsonschema.validate(config, self._schema)
        except jsonschema.exceptions.ValidationError as e:
            logger.error(f"Configuration validation error: {e.message}")
            raise ConfigError(f"Configuration validation error: {e.message}")

    async def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        try:
            keys = key.split('.')
            value = self._config
            
            for k in keys:
                value = value.get(k)
                if value is None:
                    return default
                    
            return value
            
        except Exception:
            return default

    async def set(self, key: str, value: Any, save: bool = True) -> None:
        """Set configuration value"""
        try:
            # Update config
            keys = key.split('.')
            config = self._config
            
            for k in keys[:-1]:
                config = config.setdefault(k, {})
                
            config[keys[-1]] = value
            
            # Validate new config
            self._validate_config(self._config)
            
            # Add to pending changes
            self._pending_changes[key] = value
            
            # Save if requested
            if save:
                await self.save()
                
            # Notify watchers
            await self._notify_watchers(key, value)
            
        except Exception as e:
            raise ConfigError(f"Failed to set config: {str(e)}")

    async def save(self) -> None:
        """Save configuration to file"""
        try:
            # Create parent directories if needed
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save config
            with open(self._config_path, 'w') as f:
                if self._config_path.suffix == '.json':
                    json.dump(self._config, f, indent=2)
                else:
                    yaml.safe_dump(self._config, f, indent=2)
                    
            # Clear pending changes
            self._pending_changes.clear()
            
            # Update last modified time
            self._last_modified = self._config_path.stat().st_mtime
            
        except Exception as e:
            raise ConfigError(f"Failed to save config: {str(e)}")

    async def watch(self, key: str, callback: callable) -> None:
        """Watch for configuration changes"""
        self._watchers[key] = callback

    async def unwatch(self, key: str) -> None:
        """Remove configuration watcher"""
        self._watchers.pop(key, None)

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self._config_path.exists():
                mtime = self._config_path.stat().st_mtime
                
                if mtime > self._last_modified:
                    # Reload config
                    new_config = self._load_config()
                    
                    # Find changed values
                    changes = self._get_config_changes(self._config, new_config)
                    
                    # Update config
                    self._config = new_config
                    self._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def initialize(self) -> None:
        """Initialize configuration manager"""
        try:
            # Start file watcher
            await self._file_watcher()
            
        except Exception as e:
            raise ConfigError(f"Initialization failed: {str(e)}")

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        observer = Observer()
        event_handler = ConfigFileHandler(self)
        observer.schedule(event_handler, str(self._config_path.parent), recursive=False)
        observer.start()
        logger.info("Started configuration file watcher.")

    def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    def cleanup(self) -> None:
        """Cleanup configuration manager"""
        for observer in self._observers:
            observer.stop()
        for observer in self._observers:
            observer.join()

class ConfigFileHandler(FileSystemEventHandler):
    """Configuration file change handler"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager

    def on_modified(self, event):
        if not event.is_directory:
            self.config_manager.reload_config()

    def on_created(self, event):
        if not event.is_directory:
            self.config_manager.reload_config()

    def on_deleted(self, event):
        if not event.is_directory:
            self.config_manager.reload_config()

    def on_moved(self, event):
        if not event.is_directory:
            self.config_manager.reload_config()

    def on_error(self, event):
        logger.error(f"Error in configuration file watcher: {event.strerror}")

    def on_closed(self, event):
        logger.info("Configuration file watcher closed.")

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        if key.lower().endswith(('password', 'secret', 'key')):
            logger.info(f"Configuration '{key}' updated securely.")
        else:
            logger.info(f"Configuration '{key}' updated to '{value}'.")

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

    def _get_config_changes(self, old: Dict, new: Dict, prefix: str = '') -> Dict:
        """Get configuration changes between versions"""
        changes = {}
        
        for key, value in new.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if key not in old:
                changes[full_key] = value
            elif isinstance(value, dict) and isinstance(old[key], dict):
                changes.update(
                    self._get_config_changes(old[key], value, f"{full_key}.")
                )
            elif value != old[key]:
                changes[full_key] = value
                
        return changes

    async def _file_watcher(self) -> None:
        """Watch for configuration file changes"""
        await self._check_file_changes()
        await asyncio.sleep(5)  # Check every 5 seconds

    async def _notify_changes(self, key: str, value: Any) -> None:
        """Notify configuration changes"""
        self.config_manager.logger.info(f"Configuration changed: {key}")
        # Implement change notification system here

    async def _notify_watchers(self, key: str, value: Any) -> None:
        """Notify configuration watchers"""
        try:
            # Find matching watchers
            for watch_key, callback in self.config_manager._watchers.items():
                if key.startswith(watch_key):
                    await callback(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Watcher notification failed: {str(e)}")

    async def _check_file_changes(self) -> None:
        """Check for configuration file changes"""
        try:
            if self.config_manager._config_path.exists():
                mtime = self.config_manager._config_path.stat().st_mtime
                
                if mtime > self.config_manager._last_modified:
                    # Reload config
                    new_config = self.config_manager._load_config()
                    
                    # Find changed values
                    changes = self.config_manager._get_config_changes(self.config_manager._config, new_config)
                    
                    # Update config
                    self.config_manager._config = new_config
                    self.config_manager._last_modified = mtime
                    
                    # Notify watchers
                    for key, value in changes.items():
                        await self._notify_watchers(key, value)
                    
        except Exception as e:
            self.config_manager.logger.error(f"Config file check failed: {str(e)}")

            self.config_manager.reload_config() 