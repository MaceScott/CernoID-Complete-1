"""
Centralized error handling with better structure and reusability.
"""
from typing import Type, Callable, Any, Optional, Dict, Tuple
from fastapi import HTTPException, status
import logging
from functools import wraps

logger = logging.getLogger(__name__)

class AppErrorCode:
    """Centralized error codes"""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTH_ERROR = "AUTH_ERROR"
    NOT_FOUND = "NOT_FOUND"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    RECOGNITION_ERROR = "RECOGNITION_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    NOTIFICATION_ERROR = "NOTIFICATION_ERROR"

class AppError(Exception):
    """Enhanced base application error"""
    def __init__(self, 
                 message: str,
                 code: str,
                 status_code: int = 500,
                 details: Optional[Dict] = None):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

def handle_exceptions(
    error_map: Dict[Type[Exception], Tuple[str, str, int]] = None,
    default_status: int = 500
) -> Callable:
    """
    Enhanced error handling decorator with mapping
    """
    error_map = error_map or {}
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_info = error_map.get(type(e))
                if error_info:
                    message, code, status = error_info
                    raise AppError(message, code, status)
                
                logger.exception(f"Unhandled error in {func.__name__}")
                raise AppError(str(e), "INTERNAL_ERROR", default_status)
        return wrapper
    return decorator

class ConfigurationError(AppError):
    """Configuration error"""
    pass

class SecurityError(AppError):
    """Security error"""
    pass 