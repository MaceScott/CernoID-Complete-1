from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime

class PersonBase(BaseModel):
    name: str = Field(..., description="Full name of the person")
    email: EmailStr = Field(..., description="Email address of the person")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata about the person")

class PersonCreate(PersonBase):
    pass

class PersonUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Full name of the person")
    email: Optional[EmailStr] = Field(None, description="Email address of the person")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata about the person")

class PersonResponse(PersonBase):
    id: str = Field(..., description="Unique identifier of the person")
    created_at: datetime = Field(..., description="Timestamp when the person was created")
    updated_at: datetime = Field(..., description="Timestamp when the person was last updated")
    face_encodings: Optional[list] = Field(default=None, description="List of face encodings associated with the person")
    face_count: int = Field(default=0, description="Number of face encodings associated with the person") 