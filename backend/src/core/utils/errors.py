"""Error handling utilities."""
import functools
import logging
from typing import Any, Callable, TypeVar

from src.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T', bound=Callable[..., Any])

class ApplicationError(Exception):
    """Base application error."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class DatabaseError(ApplicationError):
    """Database related errors."""
    def __init__(self, message: str):
        super().__init__(message, status_code=500)

class ValidationError(ApplicationError):
    """Validation errors."""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)

def handle_errors(logger: logging.Logger | None = None) -> Callable[[T], T]:
    """Error handling decorator."""
    def decorator(func: T) -> T:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except ApplicationError as e:
                if logger:
                    logger.error(f"{func.__name__} failed: {str(e)}")
                raise
            except Exception as e:
                if logger:
                    logger.exception(f"Unexpected error in {func.__name__}: {str(e)}")
                raise ApplicationError(
                    f"Internal server error: {str(e)}",
                    status_code=500
                )
        return wrapper  # type: ignore
    return decorator

class AuthenticationError(ApplicationError):
    """Exception raised for authentication errors."""
    def __init__(self, message: str):
        super().__init__(message, status_code=401)

class AuthorizationError(ApplicationError):
    """Exception raised for authorization errors."""
    def __init__(self, message: str):
        super().__init__(message, status_code=403)

class NotFoundError(ApplicationError):
    """Exception raised when a resource is not found."""
    def __init__(self, message: str):
        super().__init__(message, status_code=404)

class ConflictError(ApplicationError):
    """Exception raised when there's a conflict with existing data."""
    def __init__(self, message: str):
        super().__init__(message, status_code=409)

class ServiceError(ApplicationError):
    """Exception raised for service-level errors."""
    def __init__(self, message: str):
        super().__init__(message, status_code=503) 