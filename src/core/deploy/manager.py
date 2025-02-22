from typing import Dict, Optional, List
import os
import yaml
import json
from pathlib import Path
import shutil
import tempfile
from ..base import BaseComponent
from ..utils.errors import handle_errors

class DeploymentManager(BaseComponent):
    """Deployment and environment management"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._env_path = Path(self.config.get('deploy.env_path', '.env'))
        self._config_path = Path(
            self.config.get('deploy.config_path', 'config')
        )
        self._environments: Dict[str, Dict] = {}
        self._current_env: Optional[str] = None

    async def initialize(self) -> None:
        """Initialize deployment manager"""
        # Load environments
        await self._load_environments()
        
        # Set current environment
        self._current_env = os.getenv('APP_ENV', 'development')
        
        # Create environment files
        await self._create_env_files()

    async def cleanup(self) -> None:
        """Cleanup deployment resources"""
        self._environments.clear()

    @handle_errors(logger=None)
    async def _load_environments(self) -> None:
        """Load environment configurations"""
        if not self._config_path.exists():
            return
            
        # Load each environment config
        for config_file in self._config_path.glob('*.yml'):
            env_name = config_file.stem
            with open(config_file) as f:
                self._environments[env_name] = yaml.safe_load(f)

    @handle_errors(logger=None)
    async def _create_env_files(self) -> None:
        """Create environment files"""
        if not self._current_env:
            return
            
        env_config = self._environments.get(self._current_env, {})
        
        # Create .env file
        env_vars = []
        for key, value in env_config.get('environment', {}).items():
            env_vars.append(f"{key}={value}")
            
        if env_vars:
            with open(self._env_path, 'w') as f:
                f.write('\n'.join(env_vars))

    def get_config(self, env: Optional[str] = None) -> Dict:
        """Get environment configuration"""
        env = env or self._current_env
        return self._environments.get(env, {})

    def set_environment(self, env: str) -> None:
        """Set current environment"""
        if env not in self._environments:
            raise ValueError(f"Unknown environment: {env}")
            
        self._current_env = env
        os.environ['APP_ENV'] = env

    async def create_environment(self,
                               name: str,
                               config: Dict) -> None:
        """Create new environment"""
        if name in self._environments:
            raise ValueError(f"Environment already exists: {name}")
            
        # Save configuration
        config_file = self._config_path / f"{name}.yml"
        self._config_path.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
            
        self._environments[name] = config

    async def update_environment(self,
                               name: str,
                               config: Dict) -> None:
        """Update environment configuration"""
        if name not in self._environments:
            raise ValueError(f"Unknown environment: {name}")
            
        # Update configuration
        config_file = self._config_path / f"{name}.yml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
            
        self._environments[name] = config

    async def delete_environment(self, name: str) -> None:
        """Delete environment"""
        if name not in self._environments:
            raise ValueError(f"Unknown environment: {name}")
            
        # Remove configuration file
        config_file = self._config_path / f"{name}.yml"
        config_file.unlink(missing_ok=True)
        
        del self._environments[name]

    def get_environment_vars(self,
                           env: Optional[str] = None) -> Dict[str, str]:
        """Get environment variables"""
        env = env or self._current_env
        config = self._environments.get(env, {})
        return config.get('environment', {})

    def export_environment(self,
                         env: Optional[str] = None,
                         format: str = 'json') -> str:
        """Export environment configuration"""
        env = env or self._current_env
        config = self._environments.get(env, {})
        
        if format == 'json':
            return json.dumps(config, indent=2)
        elif format == 'yaml':
            return yaml.dump(config)
        else:
            raise ValueError(f"Unsupported format: {format}")

    async def import_environment(self,
                               name: str,
                               config_str: str,
                               format: str = 'json') -> None:
        """Import environment configuration"""
        try:
            if format == 'json':
                config = json.loads(config_str)
            elif format == 'yaml':
                config = yaml.safe_load(config_str)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
            await self.create_environment(name, config)
            
        except Exception as e:
            raise ValueError(f"Invalid configuration: {str(e)}") 