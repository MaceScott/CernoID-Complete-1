"""
Decorator utilities.
"""

import functools
import logging
from typing import Any, Callable, TypeVar, Optional

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

T = TypeVar('T')

def handle_errors(func: Optional[Callable[..., T]] = None, *, logger: Optional[logging.Logger] = None) -> Callable[..., T]:
    """
    Decorator to handle errors in functions.
    
    Args:
        func: The function to wrap.
        logger: Optional logger to use. If None, uses the default logger.
        
    Returns:
        The wrapped function.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                # Re-raise HTTP exceptions as they are already properly formatted
                raise
            except Exception as e:
                # Log the error
                log = logger or globals()['logger']
                log.exception(f"Error in {func.__name__}: {str(e)}")
                # Raise a 500 error
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="An internal server error occurred."
                )
        return wrapper

    if func is None:
        return decorator
    return decorator(func) 