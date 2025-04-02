import sys
import logging
from typing import Optional
from .validate import validate_env, settings

logger = logging.getLogger(__name__)

def check_environment() -> Optional[bool]:
    """
    Validate environment variables and configuration at startup.
    
    Returns:
        bool: True if validation successful, False otherwise
    """
    try:
        # Validate environment variables
        validation_result = validate_env()
        
        if not validation_result["success"]:
            logger.error("Environment validation failed:")
            logger.error(validation_result["error"])
            return False
            
        # Log successful validation
        logger.info("Environment validation successful")
        
        # Log important configuration values (excluding sensitive data)
        config = validation_result["settings"]
        logger.info(f"Environment: {config.ENVIRONMENT}")
        logger.info(f"Debug mode: {config.DEBUG}")
        logger.info(f"Face recognition enabled: {config.ENABLE_FACE_RECOGNITION}")
        logger.info(f"GPU enabled: {config.GPU_ENABLED}")
        logger.info(f"Metrics enabled: {config.ENABLE_METRICS}")
        logger.info(f"Tracing enabled: {config.ENABLE_TRACING}")
        
        return True
        
    except Exception as e:
        logger.error(f"Startup validation failed: {str(e)}")
        return False

def validate_startup() -> None:
    """
    Validate environment and configuration at startup.
    Exits the application if validation fails.
    """
    if not check_environment():
        logger.error("Startup validation failed. Application cannot start.")
        sys.exit(1)
        
    logger.info("Startup validation successful. Application can proceed.") 