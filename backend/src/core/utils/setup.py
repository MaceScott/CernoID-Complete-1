"""Application setup utilities."""
import os
from pathlib import Path
from dotenv import load_dotenv
import json
from typing import Optional

def get_app_dir() -> Path:
    """Get the application directory."""
    return Path.home() / '.cernoid'

def setup_directories(app_dir: Optional[Path] = None) -> Path:
    """Setup application directories."""
    if app_dir is None:
        app_dir = get_app_dir()
    
    # Create required directories
    dirs = [
        app_dir,
        app_dir / 'logs',
        app_dir / 'data',
        app_dir / 'data/images',
        app_dir / 'config',
        app_dir / 'models',
        app_dir / 'static'
    ]
    for dir_path in dirs:
        dir_path.mkdir(exist_ok=True)
        
    return app_dir

def load_environment(app_dir: Path) -> None:
    """Load environment variables."""
    # Load environment variables
    env_file = app_dir / '.env'
    if env_file.exists():
        load_dotenv(env_file)
    
    # Set default environment variables if not set
    if not os.getenv('ENVIRONMENT'):
        os.environ['ENVIRONMENT'] = 'development'
    if not os.getenv('DEBUG'):
        os.environ['DEBUG'] = 'false'

def create_default_config(app_dir: Path) -> None:
    """Create default configuration file."""
    config = {
        "database": {
            "host": "localhost",
            "port": 5432,
            "name": "cernoid",
            "user": "postgres",
            "password": "postgres"
        },
        "face_recognition": {
            "min_face_size": 64,
            "matching_threshold": 0.6,
            "cache_size": 1000,
            "cache_ttl": 3600
        },
        "logging": {
            "level": "INFO",
            "file": "logs/app.log"
        },
        "server": {
            "host": "0.0.0.0",
            "port": 8000,
            "workers": "auto"
        }
    }
    
    config_path = app_dir / 'config' / 'config.json'
    if not config_path.exists():
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4) 