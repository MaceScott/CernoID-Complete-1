import logging
import sys
from pathlib import Path
from typing import Optional
from core.config import config

def setup_logging(log_file: Optional[str] = None) -> None:
    """Set up logging configuration."""
    log_level = getattr(logging, config.get('LOG_LEVEL', 'INFO').upper())
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            *([logging.FileHandler(log_file)] if log_file else [])
        ]
    )
    
    # Set specific log levels for third-party libraries
    logging.getLogger('uvicorn').setLevel(logging.INFO)
    logging.getLogger('uvicorn.access').setLevel(logging.INFO)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('redis').setLevel(logging.WARNING)
    
def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name."""
    return logging.getLogger(name)

# Set up logging on module import
setup_logging('logs/app.log') 