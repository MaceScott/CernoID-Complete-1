from functools import wraps
from typing import Callable, Any, Optional
from core.logging import get_logger
from core.utils.errors import AppError, ServiceError

logger = get_logger(__name__)

def handle_exceptions(logger_func: Optional[Callable] = None) -> Callable:
    """
    Decorator to handle exceptions in functions.
    Logs the error and raises appropriate exceptions.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except AppError as e:
                if logger_func:
                    logger_func(f"Application error in {func.__name__}: {str(e)}")
                raise
            except Exception as e:
                if logger_func:
                    logger_func(f"Unexpected error in {func.__name__}: {str(e)}")
                raise ServiceError(f"An unexpected error occurred: {str(e)}")
        return wrapper
    return decorator

class FaceRecognitionError(AppError):
    """Exception raised for face recognition errors."""
    def __init__(self, message: str):
        super().__init__(message, status_code=500)

class ModelLoadError(FaceRecognitionError):
    """Exception raised when face recognition models fail to load."""
    def __init__(self, message: str):
        super().__init__(f"Failed to load face recognition model: {message}")

class FaceDetectionError(FaceRecognitionError):
    """Exception raised when face detection fails."""
    def __init__(self, message: str):
        super().__init__(f"Face detection failed: {message}")

class FaceEncodingError(FaceRecognitionError):
    """Exception raised when face encoding fails."""
    def __init__(self, message: str):
        super().__init__(f"Face encoding failed: {message}")

class FaceMatchingError(FaceRecognitionError):
    """Exception raised when face matching fails."""
    def __init__(self, message: str):
        super().__init__(f"Face matching failed: {message}")

class ImageProcessingError(FaceRecognitionError):
    """Exception raised when image processing fails."""
    def __init__(self, message: str):
        super().__init__(f"Image processing failed: {message}")

class GPUError(FaceRecognitionError):
    """Exception raised for GPU-related errors."""
    def __init__(self, message: str):
        super().__init__(f"GPU error: {message}")

class ResourceError(FaceRecognitionError):
    """Exception raised when system resources are insufficient."""
    def __init__(self, message: str):
        super().__init__(f"Resource error: {message}")

class ValidationError(FaceRecognitionError):
    """Exception raised for validation errors."""
    def __init__(self, message: str):
        super().__init__(f"Validation error: {message}")

class ConfigurationError(FaceRecognitionError):
    """Exception raised for configuration errors."""
    def __init__(self, message: str):
        super().__init__(f"Configuration error: {message}")

# Usage example:
@handle_exceptions(logger=custom_logger.error)
async def process_image(image_path: str):
    # Processing logic here
    pass 