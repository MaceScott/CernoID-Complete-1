import pytest
from fastapi import status
from src.core.errors.base import (
    BaseError,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    NotFoundError,
    ConflictError,
    RateLimitError,
    DatabaseError,
    ExternalServiceError
)

def test_base_error():
    """Test base error class."""
    error = BaseError(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Test error",
        error_code="TEST_ERROR",
        metadata={"key": "value"}
    )
    
    assert error.status_code == status.HTTP_400_BAD_REQUEST
    assert error.detail == "Test error"
    assert error.error_code == "TEST_ERROR"
    assert error.metadata == {"key": "value"}

def test_authentication_error():
    """Test authentication error."""
    error = AuthenticationError("Invalid credentials")
    
    assert error.status_code == status.HTTP_401_UNAUTHORIZED
    assert error.detail == "Invalid credentials"
    assert error.error_code == "AUTH_ERROR"

def test_authorization_error():
    """Test authorization error."""
    error = AuthorizationError("Insufficient permissions")
    
    assert error.status_code == status.HTTP_403_FORBIDDEN
    assert error.detail == "Insufficient permissions"
    assert error.error_code == "AUTHZ_ERROR"

def test_validation_error():
    """Test validation error."""
    error = ValidationError("Invalid input data")
    
    assert error.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert error.detail == "Invalid input data"
    assert error.error_code == "VALIDATION_ERROR"

def test_not_found_error():
    """Test not found error."""
    error = NotFoundError("Resource not found")
    
    assert error.status_code == status.HTTP_404_NOT_FOUND
    assert error.detail == "Resource not found"
    assert error.error_code == "NOT_FOUND"

def test_conflict_error():
    """Test conflict error."""
    error = ConflictError("Resource already exists")
    
    assert error.status_code == status.HTTP_409_CONFLICT
    assert error.detail == "Resource already exists"
    assert error.error_code == "CONFLICT"

def test_rate_limit_error():
    """Test rate limit error."""
    error = RateLimitError("Too many requests")
    
    assert error.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert error.detail == "Too many requests"
    assert error.error_code == "RATE_LIMIT"

def test_database_error():
    """Test database error."""
    error = DatabaseError("Database connection failed")
    
    assert error.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert error.detail == "Database connection failed"
    assert error.error_code == "DATABASE_ERROR"

def test_external_service_error():
    """Test external service error."""
    error = ExternalServiceError("External API failed")
    
    assert error.status_code == status.HTTP_502_BAD_GATEWAY
    assert error.detail == "External API failed"
    assert error.error_code == "EXTERNAL_SERVICE_ERROR" 