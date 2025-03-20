"""
User service for handling user-related database operations.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ...utils.logging import get_logger
from ..models import User
from .dao import BaseDAO

class UserService(BaseDAO):
    """Service for user management operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)
        self.logger = get_logger(__name__)

    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a user by their email address.
        
        Args:
            email: The email address to search for
            
        Returns:
            Dict containing user data if found, None otherwise
        """
        try:
            user = await self.get_by_criteria({'email': email})
            if not user:
                return None
                
            return self._to_dict(user[0])
            
        except SQLAlchemyError as e:
            self.logger.error(f"Database error in get_user_by_email: {str(e)}")
            raise

    async def get_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a user by their ID.
        
        Args:
            user_id: The user ID to search for
            
        Returns:
            Dict containing user data if found, None otherwise
        """
        try:
            user = await self.get_by_id(user_id)
            if not user:
                return None
                
            return self._to_dict(user)
            
        except SQLAlchemyError as e:
            self.logger.error(f"Database error in get_user_by_id: {str(e)}")
            raise

    async def create(self, 
                    email: str,
                    hashed_password: str,
                    username: Optional[str] = None,
                    role: str = "user",
                    permissions: List[str] = None,
                    is_active: bool = True) -> Dict[str, Any]:
        """
        Create a new user.
        
        Args:
            email: User's email address
            hashed_password: Pre-hashed password
            username: Optional display name
            role: User role (default: "user")
            permissions: List of permissions (default: empty list)
            is_active: Whether the account is active (default: True)
            
        Returns:
            Dict containing created user data
        """
        try:
            user = await super().create(
                email=email,
                hashed_password=hashed_password,
                username=username,
                role=role,
                permissions=permissions or [],
                is_active=is_active,
                last_login=None
            )
            
            return self._to_dict(user)
            
        except SQLAlchemyError as e:
            self.logger.error(f"Database error in create_user: {str(e)}")
            raise

    async def update_last_login(self, user_id: int) -> bool:
        """
        Update user's last login timestamp.
        
        Args:
            user_id: ID of user to update
            
        Returns:
            True if successful, False if user not found
        """
        try:
            user = await self.update(user_id, last_login=datetime.utcnow())
            return user is not None
            
        except SQLAlchemyError as e:
            self.logger.error(f"Database error in update_last_login: {str(e)}")
            raise

    async def update(self, user_id: int, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Update user attributes.
        
        Args:
            user_id: ID of user to update
            **kwargs: Attributes to update
            
        Returns:
            Dict containing updated user data if found, None otherwise
        """
        try:
            # Filter allowed fields
            allowed_fields = {
                "email", "username", "role", "permissions",
                "is_active", "hashed_password", "last_login"
            }
            
            filtered_kwargs = {
                key: value for key, value in kwargs.items()
                if key in allowed_fields
            }
            
            user = await super().update(user_id, **filtered_kwargs)
            if not user:
                return None
                
            return self._to_dict(user)
            
        except SQLAlchemyError as e:
            self.logger.error(f"Database error in update_user: {str(e)}")
            raise

    def _to_dict(self, user: User) -> Dict[str, Any]:
        """Convert user model to dictionary"""
        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "role": user.role,
            "permissions": user.permissions,
            "is_active": user.is_active,
            "last_login": user.last_login
        } 