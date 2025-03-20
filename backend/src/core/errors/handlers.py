"""Error handling utilities."""

import logging
from functools import wraps
from typing import Any, Callable, TypeVar, cast

from .base import ApplicationError

logger = logging.getLogger(__name__)
T = TypeVar('T')

def handle_errors(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to handle errors in functions.
    
    Args:
        func: The function to wrap
        
    Returns:
        The wrapped function
    """
    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return await func(*args, **kwargs)
        except ApplicationError as e:
            logger.error(f"Application error in {func.__name__}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            raise ServiceError(f"Unexpected error: {str(e)}")
    
    @wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return func(*args, **kwargs)
        except ApplicationError as e:
            logger.error(f"Application error in {func.__name__}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            raise ServiceError(f"Unexpected error: {str(e)}")
    
    return cast(Callable[..., T], async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper) 