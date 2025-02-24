"""
Face recognition API endpoints.
"""
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, File, UploadFile, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import base64

from ..dependencies import get_current_user, get_recognition_service
from ..schemas import (
    RecognitionResult,
    ErrorResponse
)
from core.utils.errors import handle_errors
from core.security.middleware import SecurityMiddleware
from core.recognition.service import RecognitionService
from ..schemas import PersonCreate, PersonResponse
from ..schemas.recognition import (
    FaceDetectionResponse,
    FaceEncodingResponse,
    MatchResult
)
from ...core.recognition import FaceRecognitionSystem
from ...core.auth.service import AuthService
from ...core.recognition.pipeline import RecognitionPipeline
from ...core.security.auth import get_current_user
from ...utils.logging import get_logger

router = APIRouter(prefix="/recognition", tags=["recognition"])
logger = get_logger(__name__)
recognition = RecognitionPipeline()

class ImageRequest(BaseModel):
    """Image request model."""
    image: str
    options: Optional[Dict[str, Any]] = None

@router.post("/recognize/")
async def recognize_face(...):
    # Recognition route implementation

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
    recognition_service: RecognitionService = Depends(),
    security: SecurityMiddleware = Depends()
):
    """Create new person with face encoding"""
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
    recognition_service: RecognitionService = Depends(),
    security: SecurityMiddleware = Depends()
):
    """Get person details"""
    person = await recognition_service.get_person(person_id)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    return person

@router.post("/verify", response_model=RecognitionResult)
async def verify_face(
    image: UploadFile = File(...),
    person_id: int,
    recognition_service: RecognitionService = Depends(),
    security: SecurityMiddleware = Depends()
):
    """Verify face against stored person"""
    try:
        # Read and decode image
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Verify face
        result = await recognition_service.verify_face(img, person_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) 