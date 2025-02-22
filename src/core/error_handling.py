from typing import Type, Dict
from dataclasses import dataclass

@dataclass
class ErrorContext:
    error_type: Type[Exception]
    message: str
    details: Dict = None
    
class CernoIDError(Exception):
    """Base exception for all CernoID errors"""
    def __init__(self, context: ErrorContext):
        self.context = context
        super().__init__(str(context.message))

class ServiceError(CernoIDError):
    """Service-specific errors"""
    pass

class ConfigurationError(CernoIDError):
    """Configuration-related errors"""
    pass

class RecognitionError(CernoIDError):
    """Face recognition errors"""
    pass

async def handle_error(error: Exception) -> None:
    """Centralized error handling"""
    from core.logging import LogManager
    logger = LogManager().get_logger("ErrorHandler")
    
    if isinstance(error, CernoIDError):
        logger.error(f"{error.context.error_type.__name__}: {error.context.message}",
                    extra={"details": error.context.details})
    else:
        logger.error(f"Unexpected error: {str(error)}") 