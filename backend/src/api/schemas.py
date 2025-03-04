"""
Pydantic models for request/response validation.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, validator
from uuid import UUID

class ErrorResponse(BaseModel):
    """Error response schema"""
    detail: str
    code: Optional[str] = None
    
class PersonBase(BaseModel):
    """Base schema for person data"""
    name: str = Field(..., min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    department: Optional[str] = Field(None, max_length=50)
    employee_id: Optional[str] = Field(None, max_length=20)
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()

class PersonCreate(PersonBase):
    """Schema for creating a new person"""
    face_image: Optional[bytes] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class PersonUpdate(PersonBase):
    """Schema for updating a person"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    active: Optional[bool] = None

class PersonResponse(PersonBase):
    """Schema for person response"""
    id: int
    face_encoding_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    active: bool = True
    
    class Config:
        orm_mode = True

class RecognitionResult(BaseModel):
    """Schema for face recognition result"""
    person_id: Optional[int] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    matched: bool
    face_location: Optional[Dict[str, int]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None

class AccessLog(BaseModel):
    """Schema for access log entry"""
    id: int
    person_id: Optional[int]
    person_name: Optional[str]
    access_time: datetime
    access_point: str
    access_type: str = Field(..., regex='^(entry|exit)$')
    success: bool
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    class Config:
        orm_mode = True

class AccessLogFilter(BaseModel):
    """Schema for access log filtering"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    person_id: Optional[int] = None
    access_point: Optional[str] = None
    success: Optional[bool] = None

class PaginatedResponse(BaseModel):
    """Generic schema for paginated responses"""
    items: List[Any]
    total: int
    page: int
    pages: int
    per_page: int
    
    @validator('pages')
    def validate_pages(cls, v, values):
        if v < 0:
            return 0
        return v

class AuthRequest(BaseModel):
    """Schema for authentication request"""
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)

class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: int
    permissions: List[str]

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