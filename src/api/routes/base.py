"""
Base router with common functionality.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, Dict, List
from core.utils.errors import AppError
from ..dependencies import get_current_user

class BaseRouter:
    """Base class for all routers"""
    
    def __init__(self, prefix: str, tags: List[str]):
        self.router = APIRouter(prefix=prefix, tags=tags)
        self.setup_routes()
    
    def setup_routes(self):
        """Setup router endpoints"""
        raise NotImplementedError
    
    def handle_error(self, error: AppError) -> HTTPException:
        """Convert AppError to HTTPException"""
        return HTTPException(
            status_code=error.status_code,
            detail={"message": error.message, "code": error.code}
        ) 