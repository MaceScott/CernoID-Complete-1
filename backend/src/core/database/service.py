from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from ..utils.logging import get_logger
from .models import User

class DatabaseService:
    """Database service for user management operations."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._session: Optional[Session] = None

    @property
    def session(self) -> Session:
        """Get the current database session."""
        if not self._session:
            raise RuntimeError("Database session not initialized")
        return self._session

    @session.setter
    def session(self, session: Session):
        """Set the database session."""
        self._session = session

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a user by their email address.
        
        Args:
            email: The email address to search for
            
        Returns:
            Dict containing user data if found, None otherwise
        """
        try:
            user = self.session.query(User).filter(User.email == email).first()
            if not user:
                return None
                
            return {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "hashed_password": user.hashed_password,
                "role": user.role,
                "permissions": user.permissions,
                "is_active": user.is_active,
                "last_login": user.last_login
            }
            
        except SQLAlchemyError as e:
            self.logger.error(f"Database error in get_user_by_email: {str(e)}")
            raise

    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a user by their ID.
        
        Args:
            user_id: The user ID to search for
            
        Returns:
            Dict containing user data if found, None otherwise
        """
        try:
            user = self.session.query(User).filter(User.id == user_id).first()
            if not user:
                return None
                
            return {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "hashed_password": user.hashed_password,
                "role": user.role,
                "permissions": user.permissions,
                "is_active": user.is_active,
                "last_login": user.last_login
            }
            
        except SQLAlchemyError as e:
            self.logger.error(f"Database error in get_user_by_id: {str(e)}")
            raise

    async def create_user(self, 
                         email: str,
                         hashed_password: str,
                         username: Optional[str] = None,
                         role: str = "user",
                         permissions: list = None,
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
            user = User(
                email=email,
                hashed_password=hashed_password,
                username=username,
                role=role,
                permissions=permissions or [],
                is_active=is_active,
                last_login=None
            )
            
            self.session.add(user)
            self.session.commit()
            
            return {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role,
                "permissions": user.permissions,
                "is_active": user.is_active,
                "last_login": user.last_login
            }
            
        except SQLAlchemyError as e:
            self.logger.error(f"Database error in create_user: {str(e)}")
            self.session.rollback()
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
            user = self.session.query(User).filter(User.id == user_id).first()
            if not user:
                return False
                
            user.last_login = datetime.utcnow()
            self.session.commit()
            return True
            
        except SQLAlchemyError as e:
            self.logger.error(f"Database error in update_last_login: {str(e)}")
            self.session.rollback()
            raise

    async def update_user(self, user_id: int, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Update user attributes.
        
        Args:
            user_id: ID of user to update
            **kwargs: Attributes to update
            
        Returns:
            Dict containing updated user data if found, None otherwise
        """
        try:
            user = self.session.query(User).filter(User.id == user_id).first()
            if not user:
                return None
                
            # Update allowed fields
            allowed_fields = {
                "email", "username", "role", "permissions",
                "is_active", "hashed_password"
            }
            
            for key, value in kwargs.items():
                if key in allowed_fields:
                    setattr(user, key, value)
                    
            self.session.commit()
            
            return {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role,
                "permissions": user.permissions,
                "is_active": user.is_active,
                "last_login": user.last_login
            }
            
        except SQLAlchemyError as e:
            self.logger.error(f"Database error in update_user: {str(e)}")
            self.session.rollback()
            raise

    async def delete_user(self, user_id: int) -> bool:
        """
        Delete a user.
        
        Args:
            user_id: ID of user to delete
            
        Returns:
            True if user was deleted, False if not found
        """
        try:
            user = self.session.query(User).filter(User.id == user_id).first()
            if not user:
                return False
                
            self.session.delete(user)
            self.session.commit()
            return True
            
        except SQLAlchemyError as e:
            self.logger.error(f"Database error in delete_user: {str(e)}")
            self.session.rollback()
            raise
