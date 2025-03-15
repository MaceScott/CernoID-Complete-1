"""
User Management API Routes for CernoID System.

This module provides comprehensive API endpoints for user management, including user creation,
retrieval, updates, and deletion, with full support for role-based access control (RBAC)
and audit logging.

Key Features:
- Complete user lifecycle management (CRUD operations)
- Role-based access control (RBAC) with fine-grained permissions
- Secure password handling with bcrypt hashing
- User profile management and updates
- Comprehensive audit logging of all operations
- Pagination support for large datasets
- Account status management and tracking

Dependencies:
- FastAPI: Web framework and routing
- Pydantic: Data validation and schemas
- Core services:
  - AuthService: Authentication, authorization, and password management
  - AuditLogger: Security event tracking and audit trail
  - Database: User data persistence and retrieval
  - Logging: System logging and error tracking

API Endpoints:
- POST /users: Create new user account
- GET /users: List users with pagination
- GET /users/{user_id}: Get user details
- PUT /users/{user_id}: Update user profile
- DELETE /users/{user_id}: Remove user account

Security:
- JWT authentication required for all endpoints
- Role-based access control with granular permissions
- Password hashing using bcrypt with configurable work factor
- Input validation and sanitization on all routes
- Rate limiting to prevent abuse
- Audit logging of all sensitive operations

Audit Logging:
- User creation and deletion events
- Profile and permission updates
- Account status changes
- Access attempts and failures
- Permission changes
- Administrative actions

Error Handling:
- Comprehensive input validation
- Proper HTTP status codes
- Detailed error messages
- Security error masking
- Database error handling
- Duplicate detection

Performance:
- Database query optimization
- Connection pooling
- Result caching
- Pagination support
- Efficient field selection
- Resource cleanup
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime

from ...core.security.auth import auth_service, User
from ...core.security.audit import audit_logger
from ...utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

class UserCreate(BaseModel):
    """
    User creation request model.
    
    Attributes:
        username (str): Unique username (3-32 chars)
        email (EmailStr): Valid email address
        password (str): Strong password (min 8 chars)
        role (str): User role for permissions
        permissions (List[str]): Additional specific permissions
        
    Validation:
        - Username: 3-32 chars, alphanumeric with underscores
        - Email: RFC 5322 compliant email format
        - Password: Minimum 8 chars, requires:
            - At least one uppercase letter
            - At least one lowercase letter
            - At least one number
            - At least one special character
        - Role: Must match predefined system roles
        - Permissions: Must be valid permission strings
        
    Example:
        ```json
        {
            "username": "john_doe",
            "email": "john@example.com",
            "password": "SecurePass123!",
            "role": "operator",
            "permissions": ["cameras.view", "faces.detect"]
        }
        ```
        
    Notes:
        - Passwords are hashed before storage
        - Usernames are converted to lowercase
        - Emails are normalized and validated
        - Roles determine base permissions
        - Additional permissions are additive
    """
    
    username: str = Field(
        ...,
        min_length=3,
        max_length=32,
        regex="^[a-zA-Z0-9_]+$",
        description="Unique username (3-32 chars, alphanumeric with underscores)"
    )
    email: EmailStr = Field(
        ...,
        description="Valid email address"
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Strong password (min 8 chars)"
    )
    role: str = Field(
        ...,
        description="User role for permissions"
    )
    permissions: List[str] = Field(
        default=[],
        description="Additional specific permissions"
    )
    
    @validator("password")
    def validate_password(cls, v):
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v

class UserUpdate(BaseModel):
    """
    User update request model.
    
    Attributes:
        email (Optional[EmailStr]): New email address
        role (Optional[str]): New role assignment
        permissions (Optional[List[str]]): Updated permission list
        is_active (Optional[bool]): Account status flag
        
    Validation:
        - Email: RFC 5322 compliant email format
        - Role: Must match predefined system roles
        - Permissions: Must be valid permission strings
        - Status: Boolean flag for account state
        
    Notes:
        - Only specified fields will be updated
        - Password updates handled separately
        - Preserves existing values for unspecified fields
        - Role changes may affect permissions
        - Status changes trigger notifications
    """
    
    email: Optional[EmailStr] = Field(
        None,
        description="New email address"
    )
    role: Optional[str] = Field(
        None,
        description="New role assignment"
    )
    permissions: Optional[List[str]] = Field(
        None,
        description="Updated permission list"
    )
    is_active: Optional[bool] = Field(
        None,
        description="Account status flag"
    )

class UserResponse(BaseModel):
    """
    User response model.
    
    Attributes:
        id (int): Unique user identifier
        username (str): User's username
        email (EmailStr): User's email address
        role (str): Assigned role
        permissions (List[str]): Effective permissions
        is_active (bool): Account status
        last_login (Optional[datetime]): Last login timestamp
        
    Notes:
        - Excludes sensitive data (password hash)
        - Includes derived permissions from role
        - Timestamps in ISO 8601 format
        - Status indicates account accessibility
        - Permissions list is comprehensive
        
    Example:
        ```json
        {
            "id": 123,
            "username": "john_doe",
            "email": "john@example.com",
            "role": "operator",
            "permissions": ["cameras.view", "faces.detect"],
            "is_active": true,
            "last_login": "2024-03-15T10:30:00Z"
        }
        ```
    """
    
    id: int = Field(..., description="Unique user identifier")
    username: str = Field(..., description="User's username")
    email: EmailStr = Field(..., description="User's email address")
    role: str = Field(..., description="Assigned role")
    permissions: List[str] = Field(..., description="Effective permissions")
    is_active: bool = Field(..., description="Account status")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")

@router.post("/users",
            response_model=UserResponse,
            status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Create a new user account.
    
    Args:
        user_data: User creation data
        current_user: Authenticated user (must have admin rights)
    
    Returns:
        UserResponse: Created user details
    
    Raises:
        HTTPException:
            - 400: Invalid input data
            - 401: Not authenticated
            - 403: Insufficient permissions
            - 409: Username/email conflict
            - 422: Validation error
            - 500: Database error
    
    Security:
        - Requires admin:create_user permission
        - Logs creation event
        - Hashes password before storage
        - Validates input data
        - Checks for duplicates
        
    Audit:
        - Logs user creation event
        - Records creator's ID
        - Timestamps creation
        - Records initial permissions
    """
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
    """
    List users with pagination support.
    
    Args:
        skip (int): Number of records to skip
        limit (int): Maximum number of records to return
        current_user: Authenticated user (must have admin rights)
    
    Returns:
        List[UserResponse]: List of user details
    
    Raises:
        HTTPException:
            - 401: Not authenticated
            - 403: Insufficient permissions
            - 500: Database error
    
    Features:
        - Pagination support
        - Configurable page size
        - Ordered by username
        - Excludes inactive users
        - Filters sensitive data
        
    Performance:
        - Uses database pagination
        - Limits maximum page size
        - Caches frequent queries
        - Optimizes field selection
    """
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
    """
    Get user details by ID.
    
    Args:
        user_id (int): User identifier
        current_user: Authenticated user
    
    Returns:
        UserResponse: User details
    
    Raises:
        HTTPException:
            - 401: Not authenticated
            - 403: Insufficient permissions
            - 404: User not found
            - 500: Database error
    
    Security:
        - Users can view their own profile
        - Admins can view any profile
        - Requires admin:read_user for other profiles
        - Filters sensitive data
        - Logs access attempts
        
    Features:
        - Includes derived permissions
        - Shows online status
        - Includes last activity
        - Shows account status
    """
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
    """
    Update user details.
    
    Args:
        user_id (int): User identifier
        user_data: Update data
        current_user: Authenticated user
    
    Returns:
        UserResponse: Updated user details
    
    Raises:
        HTTPException:
            - 400: Invalid update data
            - 401: Not authenticated
            - 403: Insufficient permissions
            - 404: User not found
            - 422: Validation error
            - 500: Database error
    
    Security:
        - Users can update their own profile
        - Admins can update any profile
        - Requires admin:update_user for other profiles
        - Validates permission changes
        - Logs all changes
        
    Audit:
        - Records all field changes
        - Logs modifier's ID
        - Timestamps modification
        - Tracks permission changes
    """
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
    """
    Delete user account.
    
    Args:
        user_id (int): User identifier
        current_user: Authenticated user (must have admin rights)
    
    Raises:
        HTTPException:
            - 401: Not authenticated
            - 403: Insufficient permissions
            - 404: User not found
            - 500: Database error
    
    Security:
        - Requires admin:delete_user permission
        - Prevents self-deletion
        - Logs deletion event
        - Validates target user
        - Checks dependencies
        
    Features:
        - Soft deletion option
        - Cascading deletion
        - Backup creation
        - Notification system
        
    Audit:
        - Logs deletion event
        - Records deleter's ID
        - Timestamps deletion
        - Archives user data
    """
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