"""Error handling utilities."""
import functools
import logging
from typing import Any, Callable, TypeVar, cast

from core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound=Callable[..., Any])

class ApplicationError(Exception):
    """Base class for application errors."""
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)

class DatabaseError(ApplicationError):
    """Database-related errors."""
    def __init__(self, message: str):
        super().__init__(message)

class ValidationError(ApplicationError):
    """Data validation errors."""
    def __init__(self, message: str):
        super().__init__(message)

def handle_errors(func: T) -> T:
    """Decorator to handle errors in functions."""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except DatabaseError as e:
            logger.error(f"Database error in {func.__name__}: {str(e)}")
            raise
        except ValidationError as e:
            logger.error(f"Validation error in {func.__name__}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            raise ApplicationError(f"An unexpected error occurred: {str(e)}")
    return cast(T, wrapper)

class AuthenticationError(ApplicationError):
    """Exception raised for authentication errors."""
    def __init__(self, message: str):
        super().__init__(message)

class AuthorizationError(ApplicationError):
    """Exception raised for authorization errors."""
    def __init__(self, message: str):
        super().__init__(message)

class NotFoundError(ApplicationError):
    """Exception raised when a resource is not found."""
    def __init__(self, message: str):
        super().__init__(message)

class ConflictError(ApplicationError):
    """Exception raised when there's a conflict with existing data."""
    def __init__(self, message: str):
        super().__init__(message)

class ServiceError(ApplicationError):
    """Exception raised for service-level errors."""
    def __init__(self, message: str):
        super().__init__(message) 