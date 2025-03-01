"""
API routes for face recognition and access control system.
Includes endpoints for person management, face recognition, and access logs.
"""

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Query, Path, status
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from pydantic import ValidationError

from .dependencies import get_current_user, get_recognition_service
from .schemas import (
    PersonCreate, 
    PersonUpdate, 
    PersonResponse, 
    AccessLog,
    ErrorResponse,
    RecognitionResult
)
from core.error_handling import handle_api_error
from core.services.access_log import AccessLogService
from core.utils.date import validate_date_range

# Configure logging
logger = logging.getLogger(__name__)

# Create router with prefix and tags
router = APIRouter(
    prefix="/api/v1",
    tags=["recognition"],
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
    }
)

@router.post(
    "/persons/",
    response_model=PersonResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new person",
    description="Create a new person in the system with their face data"
)
@handle_api_error
async def create_person(
    person: PersonCreate,
    current_user: Dict = Depends(get_current_user),
    recognition_service: Any = Depends(get_recognition_service)
) -> PersonResponse:
    """
    Create new person with the following steps:
    1. Validate input data
    2. Check user permissions
    3. Create person record
    4. Process face data if provided
    
    Args:
        person: Person data including optional face image
        current_user: Current authenticated user
        recognition_service: Recognition service instance
        
    Returns:
        Created person details
        
    Raises:
        HTTPException: If creation fails or user lacks permission
    """
    # Check permissions
    if not current_user.get("can_create_person"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create person"
        )
    
    try:
        result = await recognition_service.create_person(
            person,
            created_by=current_user["id"]
        )
        logger.info(f"Person created: {result.id} by user {current_user['id']}")
        return result
        
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post(
    "/recognize/",
    response_model=RecognitionResult,
    summary="Recognize face",
    description="Recognize face in uploaded image"
)
@handle_api_error
async def recognize_face(
    image: UploadFile = File(..., description="Image file containing face to recognize"),
    min_confidence: float = Query(0.8, ge=0.0, le=1.0, description="Minimum confidence threshold for recognition"),
    recognition_service: Any = Depends(get_recognition_service)
) -> JSONResponse:
    """Recognize face in uploaded image and return JSON response."""
    if not image.content_type.startswith("image/"):
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": "File must be an image"})

    try:
        contents = await image.read()
        result = await recognition_service.recognize_face(contents, min_confidence=min_confidence)

        if not result:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "No face recognized in image"})

        return JSONResponse(status_code=status.HTTP_200_OK, content=result.dict())

    except Exception as e:
        logger.error(f"Recognition error: {str(e)}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": str(e)})

@router.get(
    "/access-logs/",
    response_model=List[AccessLog],
    summary="Get access logs",
    description="Get access logs with optional filtering"
)
@handle_api_error
async def get_access_logs(
    start_date: Optional[datetime] = Query(
        None,
        description="Start date for log filtering (ISO format)"
    ),
    end_date: Optional[datetime] = Query(
        None,
        description="End date for log filtering (ISO format)"
    ),
    person_id: Optional[int] = Query(
        None,
        description="Filter logs by person ID"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: Dict = Depends(get_current_user)
) -> List[AccessLog]:
    """
    Get access logs with optional filtering and pagination
    
    Args:
        start_date: Optional start date filter
        end_date: Optional end date filter
        person_id: Optional person ID filter
        page: Page number for pagination
        page_size: Items per page
        current_user: Current authenticated user
        
    Returns:
        List of access logs matching criteria
        
    Raises:
        HTTPException: If retrieval fails or parameters are invalid
    """
    # Check permissions
    if not current_user.get("can_view_logs"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view logs"
        )
    
    try:
        # Validate date range if provided
        if start_date and end_date:
            validate_date_range(start_date, end_date)
        
        # Get logs with pagination
        logs = await AccessLogService.get_logs(
            start_date=start_date,
            end_date=end_date,
            person_id=person_id,
            page=page,
            page_size=page_size
        )
        
        return logs
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# Additional helper endpoints

@router.get(
    "/persons/{person_id}",
    response_model=PersonResponse,
    summary="Get person details",
    description="Get detailed information about a person"
)
@handle_api_error
async def get_person(
    person_id: int = Path(..., description="The ID of the person to retrieve"),
    recognition_service: Any = Depends(get_recognition_service),
    current_user: Dict = Depends(get_current_user)
) -> PersonResponse:
    """Get person details by ID"""
    result = await recognition_service.get_person(person_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    return result 