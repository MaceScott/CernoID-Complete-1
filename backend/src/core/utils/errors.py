"""
Error handling utilities.
"""

import functools
import logging
from typing import Any, Callable, TypeVar

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

T = TypeVar('T')

class MatcherError(Exception):
    """Error raised by the face matcher component."""
    pass

def handle_errors(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to handle errors in functions.
    
    Args:
        func: The function to wrap.
        
    Returns:
        The wrapped function.
    """
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            # Re-raise HTTP exceptions as they are already properly formatted
            raise
        except Exception as e:
            # Log the error
            logger.exception(f"Error in {func.__name__}: {str(e)}")
            # Raise a 500 error
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An internal server error occurred."
            )
    return wrapper 