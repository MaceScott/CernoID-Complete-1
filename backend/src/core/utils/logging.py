"""
Logging configuration and setup.
"""

import logging
import sys
from typing import Optional

import structlog
from pythonjsonlogger import jsonlogger

from .config import Config

def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: The name of the logger.
        
    Returns:
        structlog.BoundLogger: A configured logger instance.
    """
    return structlog.get_logger(name)

def setup_logging(config: Optional[Config] = None) -> None:
    """
    Set up logging configuration for the application.
    
    Args:
        config: Optional configuration object.
    """
    log_level = getattr(config, 'LOG_LEVEL', 'INFO') if config else 'INFO'
    
    # Configure standard logging
    logging.basicConfig(
        format='%(asctime)s [%(levelname)s] %(message)s',
        level=getattr(logging, log_level),
        stream=sys.stdout
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.render_to_log_kwargs,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Set up JSON logging handler
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Add handler to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(handler) 