"""
FastAPI dependency injection functions.
"""
from typing import Optional, Dict, AsyncGenerator, Type, Any, Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth.manager import AuthManager
from src.core.database.models.models import User
from src.core.database import db_pool
from src.core.face_recognition.core import FaceRecognitionSystem
from src.core.logging import get_logger

logger = get_logger(__name__)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Initialize managers
auth_manager = AuthManager()
recognition_service = FaceRecognitionSystem()

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

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    session = db_pool.get_session()
    try:
        yield session
    finally:
        session.close()

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """Get current authenticated user."""
    try:
        user = await auth_manager.get_current_user(token, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_recognition_service() -> FaceRecognitionSystem:
    """Get recognition service instance."""
    return recognition_service

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