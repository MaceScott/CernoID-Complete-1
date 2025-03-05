from functools import wraps
from typing import Callable, Any
from fastapi import HTTPException, status
from core.logging import get_logger

logger = get_logger(__name__)

def handle_errors(func: Callable) -> Callable:
    """
    Decorator to handle errors in FastAPI endpoints and other functions.
    Logs the error and returns appropriate HTTP responses.
    """
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except HTTPException as e:
            logger.error(f"HTTP error in {func.__name__}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )
    return wrapper

class AppError(Exception):
    """Base exception class for application errors."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class ValidationError(AppError):
    """Exception raised for validation errors."""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)

class AuthenticationError(AppError):
    """Exception raised for authentication errors."""
    def __init__(self, message: str):
        super().__init__(message, status_code=401)

class AuthorizationError(AppError):
    """Exception raised for authorization errors."""
    def __init__(self, message: str):
        super().__init__(message, status_code=403)

class NotFoundError(AppError):
    """Exception raised when a resource is not found."""
    def __init__(self, message: str):
        super().__init__(message, status_code=404)

class ConflictError(AppError):
    """Exception raised when there's a conflict with existing data."""
    def __init__(self, message: str):
        super().__init__(message, status_code=409)

class ServiceError(AppError):
    """Exception raised for service-level errors."""
    def __init__(self, message: str):
        super().__init__(message, status_code=503) 