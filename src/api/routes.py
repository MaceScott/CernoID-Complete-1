from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from typing import List, Optional
from datetime import datetime
from .dependencies import get_current_user, get_recognition_service
from .schemas import PersonCreate, PersonUpdate, PersonResponse

router = APIRouter()

@router.post("/persons/", response_model=PersonResponse)
async def create_person(
    person: PersonCreate,
    current_user = Depends(get_current_user),
    recognition_service = Depends(get_recognition_service)
):
    """Create new person in the system"""
    try:
        result = await recognition_service.create_person(person)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/recognize/")
async def recognize_face(
    image: UploadFile = File(...),
    recognition_service = Depends(get_recognition_service)
):
    """Recognize face in uploaded image"""
    try:
        contents = await image.read()
        result = await recognition_service.recognize_face(contents)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/access-logs/", response_model=List[AccessLog])
async def get_access_logs(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    person_id: Optional[int] = None,
    current_user = Depends(get_current_user)
):
    """Get access logs with optional filters"""
    try:
        logs = await AccessLogService.get_logs(
            start_date=start_date,
            end_date=end_date,
            person_id=person_id
        )
        return logs
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 