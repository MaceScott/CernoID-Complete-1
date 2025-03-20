"""
Application setup package.
Contains functions for initializing the application environment and configuration.
"""

from .app import (
    get_app_dir,
    setup_directories,
    load_environment,
    create_default_config
)

__all__ = [
    'get_app_dir',
    'setup_directories',
    'load_environment',
    'create_default_config'
] 