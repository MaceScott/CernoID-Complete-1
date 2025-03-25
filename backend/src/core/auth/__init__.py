"""
Authentication module for user authentication and authorization.
"""
from .service import AuthService
from .dependencies import get_current_user
from core.database.models.models import User
from .manager import AuthManager

# Create a singleton instance
auth_service = AuthService()

__all__ = [
    'AuthService',
    'auth_service',
    'get_current_user',
    'User',
    'AuthManager'
] 