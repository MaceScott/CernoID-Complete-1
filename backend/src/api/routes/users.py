"""
User management API endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from datetime import datetime

from ...core.security.auth import auth_service, User
from ...core.security.audit import audit_logger
from ...utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

class UserCreate(BaseModel):
    """User creation model."""
    username: str
    email: EmailStr
    password: str
    role: str
    permissions: List[str] = []

class UserUpdate(BaseModel):
    """User update model."""
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    """User response model."""
    id: int
    username: str
    email: EmailStr
    role: str
    permissions: List[str]
    is_active: bool
    last_login: Optional[datetime]

@router.post("/users",
            response_model=UserResponse,
            status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Create new user."""
    try:
        # Check admin permission
        if not await auth_service.check_permission(
            current_user, "admin:create_user"
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
            
        # Create user
        new_user = await auth_service.db.create_user({
            "username": user_data.username,
            "email": user_data.email,
            "password": auth_service.create_password_hash(user_data.password),
            "role": user_data.role,
            "permissions": user_data.permissions,
            "is_active": True
        })
        
        # Log event
        await audit_logger.log_event(
            event_type="user_management",
            user_id=current_user.id,
            resource="users",
            action="create",
            details={"created_user_id": new_user.id}
        )
        
        return new_user
        
    except Exception as e:
        logger.error(f"User creation failed: {str(e)}")
        raise

@router.get("/users",
           response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(auth_service.get_current_user)
):
    """List users with pagination."""
    try:
        # Check permission
        if not await auth_service.check_permission(
            current_user, "admin:list_users"
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
            
        return await auth_service.db.list_users(skip, limit)
        
    except Exception as e:
        logger.error(f"User listing failed: {str(e)}")
        raise

@router.get("/users/{user_id}",
           response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Get user by ID."""
    try:
        # Check permissions
        if not (
            current_user.id == user_id or
            await auth_service.check_permission(current_user, "admin:read_user")
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
            
        user = await auth_service.db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        return user
        
    except Exception as e:
        logger.error(f"User retrieval failed: {str(e)}")
        raise

@router.put("/users/{user_id}",
           response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Update user."""
    try:
        # Check permissions
        if not (
            current_user.id == user_id or
            await auth_service.check_permission(current_user, "admin:update_user")
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
            
        # Update user
        updated_user = await auth_service.db.update_user(
            user_id,
            user_data.dict(exclude_unset=True)
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        # Log event
        await audit_logger.log_event(
            event_type="user_management",
            user_id=current_user.id,
            resource="users",
            action="update",
            details={
                "updated_user_id": user_id,
                "changes": user_data.dict(exclude_unset=True)
            }
        )
        
        return updated_user
        
    except Exception as e:
        logger.error(f"User update failed: {str(e)}")
        raise

@router.delete("/users/{user_id}",
              status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Delete user."""
    try:
        # Check admin permission
        if not await auth_service.check_permission(
            current_user, "admin:delete_user"
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
            
        # Delete user
        success = await auth_service.db.delete_user(user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        # Log event
        await audit_logger.log_event(
            event_type="user_management",
            user_id=current_user.id,
            resource="users",
            action="delete",
            details={"deleted_user_id": user_id}
        )
        
    except Exception as e:
        logger.error(f"User deletion failed: {str(e)}")
        raise 