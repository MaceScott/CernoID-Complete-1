"""Base error types for the application."""

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