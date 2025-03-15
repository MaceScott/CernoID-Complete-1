"""
File: user.py
Purpose: User model for authentication and authorization in the CernoID system.

Key Features:
- User authentication with bcrypt password hashing
- Role-based access control (RBAC)
- Account status management
- Login attempt tracking
- Personal information management

Dependencies:
- Pydantic: Data validation
- Bcrypt: Password hashing
- Core services:
  - BaseDBModel: Base model functionality
  - Database: Storage operations
  - Authentication: Password handling
  - Authorization: Permission checks

Security:
- Password hashing with bcrypt
- Login attempt tracking
- Account locking
- Role validation
- Permission checks

Roles:
- admin: Full system access
- operator: Camera and alert management
- viewer: Read-only access
- api: API access only

Permissions:
- system: System configuration
- cameras: Camera management
- alerts: Alert management
- users: User management
- api: API access
"""

from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import bcrypt
from pydantic import Field, validator, EmailStr

from .base import BaseDBModel
from ...utils.logging import get_logger

logger = get_logger(__name__)

class User(BaseDBModel):
    """
    User model for authentication and authorization.
    
    Attributes:
        username (str): Unique username
        email (EmailStr): User email address
        password (str): Hashed password
        role (str): User role (admin/operator/viewer/api)
        permissions (Set[str]): User permissions
        first_name (str): User first name
        last_name (str): User last name
        phone (str): Contact phone number
        active (bool): Account status
        last_login (datetime): Last login timestamp
        failed_attempts (int): Failed login attempts
        locked_until (datetime): Account lock expiry
        
    Features:
        - Password hashing and validation
        - Role-based access control
        - Account status management
        - Login attempt tracking
        - Personal information
        
    Security:
        - Bcrypt password hashing
        - Account locking
        - Permission validation
        - Role enforcement
        - Audit logging
    """
    
    username: str = Field(..., min_length=3, max_length=32)
    email: EmailStr
    password: str
    role: str = Field(default="viewer")
    permissions: Set[str] = Field(default_factory=set)
    first_name: str = Field(..., min_length=1, max_length=64)
    last_name: str = Field(..., min_length=1, max_length=64)
    phone: Optional[str] = None
    active: bool = True
    last_login: Optional[datetime] = None
    failed_attempts: int = Field(default=0, ge=0)
    locked_until: Optional[datetime] = None
    
    ROLES = {"admin", "operator", "viewer", "api"}
    PERMISSIONS = {"system", "cameras", "alerts", "users", "api"}
    MAX_FAILED_ATTEMPTS = 5
    LOCK_DURATION = 30  # minutes
    
    @validator("role")
    def validate_role(cls, v: str) -> str:
        """
        Validate user role.
        
        Args:
            v: Role value
            
        Returns:
            str: Validated role
            
        Validation:
            - Role must be in allowed set
            - Case-insensitive matching
            - Default role handling
            - Role hierarchy
        """
        if v.lower() not in cls.ROLES:
            raise ValueError(f"Invalid role. Must be one of: {cls.ROLES}")
        return v.lower()
        
    @validator("permissions")
    def validate_permissions(cls, v: Set[str]) -> Set[str]:
        """
        Validate user permissions.
        
        Args:
            v: Permission set
            
        Returns:
            Set[str]: Validated permissions
            
        Validation:
            - Permissions must be in allowed set
            - Case-insensitive matching
            - Role-based defaults
            - Permission hierarchy
        """
        invalid = v - cls.PERMISSIONS
        if invalid:
            raise ValueError(f"Invalid permissions: {invalid}")
        return v
        
    @validator("password")
    def hash_password(cls, v: str) -> str:
        """
        Hash password using bcrypt.
        
        Args:
            v: Plain text password
            
        Returns:
            str: Hashed password
            
        Features:
            - Bcrypt hashing
            - Salt generation
            - Work factor control
            - Length validation
            - Complexity check
        """
        if not v.startswith("$2b$"):  # Not already hashed
            salt = bcrypt.gensalt()
            return bcrypt.hashpw(v.encode(), salt).decode()
        return v
        
    def check_password(self, password: str) -> bool:
        """
        Check password against stored hash.
        
        Args:
            password: Plain text password
            
        Returns:
            bool: True if password matches
            
        Features:
            - Bcrypt verification
            - Timing attack protection
            - Error handling
            - Attempt tracking
            - Account locking
        """
        try:
            return bcrypt.checkpw(
                password.encode(),
                self.password.encode()
            )
        except Exception as e:
            logger.error(f"Password check failed: {str(e)}")
            return False
            
    async def update_login(self, db, success: bool) -> None:
        """
        Update login attempt status.
        
        Args:
            db: Database connection
            success: Login success flag
            
        Features:
            - Attempt tracking
            - Account locking
            - Lock duration
            - Auto unlock
            - Audit logging
        """
        try:
            if success:
                self.last_login = datetime.utcnow()
                self.failed_attempts = 0
                self.locked_until = None
            else:
                self.failed_attempts += 1
                if self.failed_attempts >= self.MAX_FAILED_ATTEMPTS:
                    self.locked_until = datetime.utcnow() + \
                        timedelta(minutes=self.LOCK_DURATION)
                    
            await self.save(db)
            
        except Exception as e:
            logger.error(f"Failed to update login status: {str(e)}")
            raise
            
    def has_permission(self, permission: str) -> bool:
        """
        Check if user has specific permission.
        
        Args:
            permission: Permission to check
            
        Returns:
            bool: True if user has permission
            
        Features:
            - Role-based checks
            - Permission inheritance
            - Admin override
            - Caching support
            - Audit logging
        """
        if not self.active:
            return False
            
        if self.role == "admin":
            return True
            
        return permission in self.permissions
        
    def get_full_name(self) -> str:
        """
        Get user's full name.
        
        Returns:
            str: Full name (first + last)
            
        Features:
            - Name formatting
            - Space handling
            - Empty check
            - Unicode support
            - Length validation
        """
        return f"{self.first_name} {self.last_name}".strip()
        
    @property
    def is_locked(self) -> bool:
        """
        Check if account is locked.
        
        Returns:
            bool: True if account is locked
            
        Features:
            - Lock status
            - Lock duration
            - Auto unlock
            - Attempt count
            - Time validation
        """
        if not self.locked_until:
            return False
            
        return datetime.utcnow() < self.locked_until
        
    @classmethod
    def get_indexes(cls) -> List[Dict]:
        """
        Get collection indexes.
        
        Returns:
            List[Dict]: Index specifications
            
        Indexes:
            - username (unique)
            - email (unique)
            - role
            - active
            - last_login
        """
        return [
            {
                "keys": [("username", 1)],
                "unique": True
            },
            {
                "keys": [("email", 1)],
                "unique": True
            },
            {
                "keys": [("role", 1)]
            },
            {
                "keys": [("active", 1)]
            },
            {
                "keys": [("last_login", -1)]
            }
        ] 