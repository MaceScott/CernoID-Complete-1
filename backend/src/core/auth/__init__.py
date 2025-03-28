"""
Authentication package.
Contains authentication and authorization related functionality.
"""

from .service import AuthService
from .dependencies import get_current_user
from core.database.models.models import User
from .manager import AuthManager
from core.config import get_settings

# Get settings instance
settings = get_settings()

# Create a singleton instance
auth_service = AuthService(settings)

# Export functions from the service instance
get_password_hash = auth_service.get_password_hash
verify_password = auth_service.verify_password
create_access_token = auth_service.create_access_token
verify_token = auth_service.verify_token
authenticate_user = auth_service.authenticate_user

__all__ = [
    'AuthService',
    'auth_service',
    'get_current_user',
    'User',
    'AuthManager',
    'get_password_hash',
    'verify_password',
    'create_access_token',
    'verify_token',
    'authenticate_user',
] 