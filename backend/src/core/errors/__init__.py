"""
Application-wide error types and error handling utilities.
"""

from .base import (
    ApplicationError,
    DatabaseError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    ServiceError
)
from .handlers import handle_errors

__all__ = [
    'ApplicationError',
    'DatabaseError',
    'ValidationError',
    'AuthenticationError',
    'AuthorizationError',
    'NotFoundError',
    'ConflictError',
    'ServiceError',
    'handle_errors'
] 