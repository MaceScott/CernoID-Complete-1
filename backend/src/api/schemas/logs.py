"""
Log-related schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class AccessLog(BaseModel):
    """Schema for access log entries."""
    id: str = Field(..., description="Unique identifier of the log entry")
    timestamp: datetime = Field(..., description="When the access occurred")
    user_id: str = Field(..., description="ID of the user who made the access")
    action: str = Field(..., description="Type of action performed")
    resource: str = Field(..., description="Resource that was accessed")
    ip_address: Optional[str] = Field(None, description="IP address of the client")
    user_agent: Optional[str] = Field(None, description="User agent string of the client")
    status_code: int = Field(..., description="HTTP status code of the response")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional details about the access")

class AccessLogFilter(BaseModel):
    """Schema for filtering access logs."""
    start_date: Optional[datetime] = Field(None, description="Start date for filtering logs")
    end_date: Optional[datetime] = Field(None, description="End date for filtering logs")
    user_id: Optional[str] = Field(None, description="User ID to filter logs")
    action: Optional[str] = Field(None, description="Action type to filter logs")
    resource: Optional[str] = Field(None, description="Resource to filter logs")
    status_code: Optional[int] = Field(None, description="Status code to filter logs") 