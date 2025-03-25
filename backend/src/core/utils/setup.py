"""
Utility functions for setting up the application environment.
"""
import os
from pathlib import Path
from typing import Dict, Any
import logging
from dotenv import load_dotenv

from ..config import settings

logger = logging.getLogger(__name__)

def setup_directories() -> None:
    """
    Create required directories for the application.
    """
    try:
        # Create required directories
        directories = [
            settings.DATA_DIR,
            settings.LOGS_DIR,
            settings.MODELS_DIR,
            settings.STATIC_DIR,
            settings.TEMP_DIR
        ]
        
        for directory in directories:
            if directory:
                os.makedirs(directory, exist_ok=True)
                logger.info(f"Created directory: {directory}")
    except Exception as e:
        logger.error(f"Failed to create directories: {e}")
        raise

def load_environment() -> Dict[str, Any]:
    """
    Load environment variables from .env file.
    """
    try:
        # Load environment variables from .env file if it exists
        env_file = Path(".env")
        if env_file.exists():
            load_dotenv(env_file)
            logger.info("Loaded environment variables from .env file")
        else:
            logger.warning("No .env file found, using default environment variables")
        
        # Return current environment variables
        return dict(os.environ)
    except Exception as e:
        logger.error(f"Failed to load environment variables: {e}")
        raise 