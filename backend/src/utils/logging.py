"""Logging utility module."""
import logging
from typing import Optional
from src.core.config.settings import get_settings

settings = get_settings()

def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """Get a logger instance with the specified name and level."""
    logger = logging.getLogger(name)
    
    if level is None:
        level = getattr(logging, settings.LOG_LEVEL.upper())
    
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger 