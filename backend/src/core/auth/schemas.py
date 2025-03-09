"""Authentication schemas."""
from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    """Token schema."""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Token data schema."""
    username: str | None = None

class UserBase(BaseModel):
    """Base user schema."""
    username: str
    email: EmailStr
    is_active: bool = True

class UserCreate(UserBase):
    """User creation schema."""
    password: str

class UserRead(UserBase):
    """User read schema."""
    id: int

    class Config:
        """Pydantic config."""
        from_attributes = True 