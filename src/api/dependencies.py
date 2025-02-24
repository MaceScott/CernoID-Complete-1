"""
FastAPI dependency injection functions.
"""
from typing import Optional, Dict, AsyncGenerator, Type, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from core.auth.manager import AuthManager
from core.recognition.core import FaceRecognitionSystem
from core.config.settings import get_settings
from core.utils.errors import AppError, AppErrorCode

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Initialize managers
auth_manager = AuthManager()
settings = get_settings()

class ServiceProvider:
    """Service provider with caching"""
    _instances: Dict[str, Any] = {}
    
    @classmethod
    async def get_service(cls, service_class: Type[Any]) -> Any:
        """Get or create service instance"""
        service_name = service_class.__name__
        if service_name not in cls._instances:
            cls._instances[service_name] = service_class()
        return cls._instances[service_name]
    
    @classmethod
    async def cleanup(cls):
        """Cleanup all services"""
        for service in cls._instances.values():
            await service.cleanup()
        cls._instances.clear()

async def get_service(service_class: Type[Any]) -> AsyncGenerator[Any, None]:
    """Generic service dependency"""
    service = await ServiceProvider.get_service(service_class)
    try:
        yield service
    finally:
        await service.cleanup()

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    """
    Get current authenticated user from token.
    
    Args:
        token: JWT token from request
        
    Returns:
        Dict containing user information
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        payload = await auth_manager.verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_recognition_service() -> FaceRecognitionSystem:
    """
    Get face recognition service instance.
    
    Returns:
        Configured FaceRecognitionSystem instance
    """
    return FaceRecognitionSystem()

async def get_admin_user(
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """
    Get current user and verify admin privileges.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Dict containing admin user information
        
    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user 