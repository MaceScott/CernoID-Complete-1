"""Face recognition specific errors."""

from ..errors.base import ApplicationError

class FaceRecognitionError(ApplicationError):
    """Base exception for face recognition errors."""
    def __init__(self, message: str):
        super().__init__(message)

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