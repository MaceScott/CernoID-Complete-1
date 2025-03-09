"""
Face recognition API endpoints.
"""
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, File, UploadFile, Query, status, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import base64
import numpy as np
import cv2

from core.auth.dependencies import get_current_user
from core.face_recognition import FaceRecognitionSystem, get_recognition_service
from core.utils.errors import handle_errors
from core.security.middleware import SecurityMiddleware
from core.auth.manager import AuthManager as AuthService
from core.logging import get_logger

from api.schemas import (
    RecognitionResult,
    ErrorResponse,
    PersonCreate,
    PersonResponse
)
from api.schemas.recognition import (
    FaceDetectionResponse,
    FaceEncodingResponse,
    MatchResult
)

router = APIRouter(prefix="/recognition", tags=["recognition"])
logger = get_logger(__name__)

class ImageRequest(BaseModel):
    """Image request model."""
    image: str
    options: Optional[Dict[str, Any]] = None

@router.post("/recognize", response_model=RecognitionResult)
async def recognize_face(
    image: UploadFile,
    recognition_service: FaceRecognitionSystem = Depends(get_recognition_service),
    current_user: Any = Depends(get_current_user)
) -> RecognitionResult:
    """
    Recognize faces in the uploaded image.
    """
    try:
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        result = await recognition_service.process_image(img)
        return result
    except Exception as e:
        logger.error(f"Face recognition failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/detect", response_model=FaceDetectionResponse)
async def detect_faces(
    image: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """Detect faces in image."""
    # Implementation

@router.post("/encode", response_model=FaceEncodingResponse)
async def create_encoding(
    image: UploadFile = File(...),
    user_id: Optional[int] = None,
    current_user = Depends(get_current_user)
):
    """Create face encoding from image."""
    # Implementation

@router.post("/match", response_model=List[MatchResult])
async def match_faces(
    image: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """Match faces against database."""
    # Implementation

@router.post("/persons", response_model=PersonResponse)
async def create_person(
    person: PersonCreate,
    recognition_service: FaceRecognitionSystem = Depends(get_recognition_service),
    current_user = Depends(get_current_user)
):
    """Create a new person with face recognition data."""
    try:
        # Create person with face
        result = await recognition_service.create_person(
            name=person.name,
            email=person.email,
            face_image=person.face_image
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/persons/{person_id}", response_model=PersonResponse)
async def get_person(
    person_id: int,
    recognition_service: FaceRecognitionSystem = Depends(get_recognition_service),
    current_user = Depends(get_current_user)
):
    """Get person by ID."""
    # Implementation
    pass

@router.post("/verify", response_model=RecognitionResult)
async def verify_face(
    image: UploadFile,
    person_id: int,
    recognition_service: FaceRecognitionSystem = Depends(get_recognition_service),
    current_user = Depends(get_current_user)
):
    """Verify face against a person's stored face encodings."""
    # Implementation
    pass 