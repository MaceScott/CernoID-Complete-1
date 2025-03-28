"""
Person management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional

from ..dependencies import get_current_user, get_recognition_service, get_admin_user
from ..schemas import (
    PersonCreate,
    PersonUpdate,
    PersonResponse,
    PaginatedResponse,
    ErrorResponse
)
from core.utils.decorators import handle_errors

router = APIRouter(prefix="/persons", tags=["persons"])

@router.post("/", response_model=PersonResponse)
async def create_person(
    person: PersonCreate,
    recognition_service = Depends(get_recognition_service),
    current_user = Depends(get_admin_user)
):
    """Create a new person."""
    try:
        return await recognition_service.create_person(person)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) 