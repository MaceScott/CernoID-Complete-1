from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str

class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    name: str

class UserCreate(UserBase):
    """User creation schema"""
    password: str

class UserResponse(UserBase):
    """User response schema"""
    id: int
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

class PersonBase(BaseModel):
    """Base person schema"""
    name: str
    email: Optional[EmailStr] = None

class PersonCreate(PersonBase):
    """Person creation schema"""
    face_image: bytes

class PersonResponse(PersonBase):
    """Person response schema"""
    id: int
    created_at: datetime
    is_active: bool
    face_count: int

    class Config:
        from_attributes = True

class RecognitionResult(BaseModel):
    """Face recognition result schema"""
    person_id: int
    confidence: float
    bbox: List[int]
    matched: bool 