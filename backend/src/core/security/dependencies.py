from typing import Optional
import logging
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from ..utils.session import session_manager
from ..utils.csrf import csrf_protection
from ..logging.config import LogConfig

logger = LogConfig().get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> dict:
    """
    Get current authenticated user.
    
    Args:
        request: FastAPI request
        token: OAuth2 token
        
    Returns:
        dict: User data
        
    Raises:
        HTTPException: If user is not authenticated
    """
    try:
        # Get client IP
        ip = request.client.host if request.client else "unknown"
        
        # Get session token from cookie
        session_token = request.cookies.get("session_token")
        
        # Validate session
        if not session_token or not session_manager.validate_session(session_token, ip):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session"
            )
            
        # Get user data from session
        user_data = session_manager.sessions[session_token]
        
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )

async def get_current_active_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Get current active user.
    
    Args:
        current_user: Current user data
        
    Returns:
        dict: Active user data
        
    Raises:
        HTTPException: If user is not active
    """
    if not current_user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

async def get_current_admin_user(
    current_user: dict = Depends(get_current_active_user)
) -> dict:
    """
    Get current admin user.
    
    Args:
        current_user: Current user data
        
    Returns:
        dict: Admin user data
        
    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def verify_csrf_token(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> None:
    """
    Verify CSRF token.
    
    Args:
        request: FastAPI request
        current_user: Current user data
        
    Raises:
        HTTPException: If CSRF token is invalid
    """
    try:
        csrf_protection.verify_csrf_token(request, current_user["user_id"])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CSRF verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CSRF verification failed"
        )

def require_permissions(*permissions: str):
    """
    Require specific permissions.
    
    Args:
        *permissions: Required permissions
        
    Returns:
        Callable: Dependency function
    """
    async def permission_checker(
        current_user: dict = Depends(get_current_active_user)
    ) -> dict:
        user_permissions = current_user.get("permissions", [])
        
        for permission in permissions:
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing permission: {permission}"
                )
                
        return current_user
        
    return permission_checker 