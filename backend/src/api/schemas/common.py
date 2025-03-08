from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Generic, TypeVar, List
from datetime import datetime

T = TypeVar('T')

class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T] = Field(..., description="List of items in the current page")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page") 