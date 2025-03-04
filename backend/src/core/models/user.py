from typing import Dict, Optional, List
from datetime import datetime
from pydantic import EmailStr, validator
from .base import BaseDBModel
from ..utils.security import hash_password

class User(BaseDBModel):
    """User model"""
    
    username: str
    email: EmailStr
    password: str
    role: str
    permissions: List[str]
    first_name: Optional[str]
    last_name: Optional[str]
    phone: Optional[str]
    active: bool = True
    last_login: Optional[datetime]
    failed_attempts: int = 0
    locked_until: Optional[datetime]
    
    @validator('role')
    def validate_role(cls, v):
        """Validate user role"""
        valid_roles = ['admin', 'supervisor', 'operator', 'viewer']
        if v not in valid_roles:
            raise ValueError(f"Invalid role: {v}")
        return v

    @validator('password')
    def hash_new_password(cls, v):
        """Hash password if not already hashed"""
        if not v.startswith('$2b$'):  # bcrypt hash prefix
            return hash_password(v)
        return v

    async def check_password(self, password: str) -> bool:
        """Check password"""
        from bcrypt import checkpw
        return checkpw(
            password.encode('utf-8'),
            self.password.encode('utf-8')
        )

    async def update_login(self, db, success: bool) -> None:
        """Update login statistics"""
        updates = {
            'last_login': datetime.utcnow() if success else None
        }
        
        if success:
            updates['failed_attempts'] = 0
            updates['locked_until'] = None
        else:
            updates['failed_attempts'] = self.failed_attempts + 1
            if updates['failed_attempts'] >= 5:
                updates['locked_until'] = datetime.utcnow().replace(
                    minute=datetime.utcnow().minute + 15
                )
        
        await db.users.update_one(
            {'id': self.id},
            {'$set': updates}
        ) 