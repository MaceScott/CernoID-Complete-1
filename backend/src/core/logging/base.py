import logging
import structlog
from pythonjsonlogger import jsonlogger
from typing import Optional

# Configure basic logging
def setup_basic_logging(level: str = "INFO") -> None:
    """Setup basic logging configuration"""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # Create JSON formatter
    formatter = jsonlogger.JsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)

# Initialize basic logging
setup_basic_logging()

def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Get a logger instance"""
    logger = logging.getLogger(name)
    if level:
        logger.setLevel(level)
    return logger 