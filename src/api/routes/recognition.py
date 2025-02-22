from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, status
from typing import List
import numpy as np
import cv2
from core.security.middleware import SecurityMiddleware
from core.recognition.service import RecognitionService
from ..schemas import PersonCreate, PersonResponse, RecognitionResult

router = APIRouter(prefix="/recognition", tags=["recognition"])

@router.post("/detect", response_model=List[RecognitionResult])
async def detect_faces(
    image: UploadFile = File(...),
    recognition_service: RecognitionService = Depends(),
    security: SecurityMiddleware = Depends()
):
    """Detect and recognize faces in image"""
    try:
        # Read and decode image
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Process image
        results = await recognition_service.detect_faces(img)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

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