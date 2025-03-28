"""
Authentication dependencies module.
"""
from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.config.settings import get_settings
from core.database.base import get_session
from core.database.models.models import User
from core.auth.service import AuthService

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_session)
) -> User:
    """Get current user from token."""
    auth_service = AuthService(settings)
    try:
        token_data = await auth_service.verify_token(token)
        query = select(User).where(User.id == token_data.user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

def require_permissions(user: User, required_permissions: str) -> None:
    """
    Check if user has required permissions.
    
    Args:
        user: User to check permissions for
        required_permissions: Required permission string
        
    Raises:
        HTTPException: If user doesn't have required permissions
    """
    if not user.has_permission(required_permissions):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        ) 