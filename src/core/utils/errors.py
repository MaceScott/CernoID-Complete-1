from typing import Optional, TypeVar, Callable, Any
from functools import wraps
import logging
import traceback
import sys
from datetime import datetime

T = TypeVar('T')

def handle_errors(
    logger: Optional[logging.Logger] = None,
    default: Any = None,
    raise_error: bool = False,
    retry_count: int = 0,
    retry_delay: float = 1.0
) -> Callable:
    """Error handling decorator"""
    
    def decorator(func: Callable[..., T]) -> Callable[..., Optional[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Optional[T]:
            nonlocal logger
            
            # Get logger from class if not provided
            if not logger and args and hasattr(args[0], 'logger'):
                logger = args[0].logger
            elif not logger:
                logger = logging.getLogger(func.__name__)

            attempts = retry_count + 1
            last_error = None

            for attempt in range(attempts):
                try:
                    return await func(*args, **kwargs)
                    
                except Exception as e:
                    last_error = e
                    exc_info = sys.exc_info()
                    
                    # Log error with context
                    error_context = {
                        'function': func.__name__,
                        'args': args,
                        'kwargs': kwargs,
                        'attempt': attempt + 1,
                        'timestamp': datetime.utcnow().isoformat(),
                        'traceback': ''.join(
                            traceback.format_exception(*exc_info)
                        )
                    }
                    
                    logger.error(
                        f"Error in {func.__name__}: {str(e)}",
                        extra={'error_context': error_context}
                    )

                    if attempt < attempts - 1:
                        await asyncio.sleep(retry_delay * (attempt + 1))
                    elif raise_error:
                        raise last_error
                        
            return default
            
        return wrapper
    return decorator

class ApplicationError(Exception):
    """Base application error"""
    
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code or 'INTERNAL_ERROR'
        super().__init__(self.message)

class ConfigurationError(ApplicationError):
    """Configuration error"""
    pass

class ValidationError(ApplicationError):
    """Validation error"""
    pass

class SecurityError(ApplicationError):
    """Security error"""
    pass 