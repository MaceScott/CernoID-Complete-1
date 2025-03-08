from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 