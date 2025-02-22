from fastapi import APIRouter, Depends, HTTPException, UploadFile
from typing import List, Optional
from core.auth.authenticator import AuthManager
from core.recognition.processor import FaceProcessor
from core.events.manager import EventManager
from core.error_handling import handle_exceptions
import cv2
import numpy as np

router = APIRouter()
auth_manager = AuthManager()
face_processor = FaceProcessor()
event_manager = EventManager()

@router.post("/process_faces")
@handle_exceptions(logger=api_logger.error)
async def process_faces(
    images: List[UploadFile],
    current_user = Depends(auth_manager.get_current_user)
):
    results = []
    for image in images:
        contents = await image.read()
        frame = cv2.imdecode(
            np.frombuffer(contents, np.uint8),
            cv2.IMREAD_COLOR
        )
        result = await face_processor.process_frame(frame)
        results.append(result)
        
        await event_manager.publish(Event(
            type='face_processed',
            data={
                'user_id': current_user.id,
                'result': result
            }
        ))
    
    return {"results": results}

@router.post("/register_face")
@handle_exceptions(logger=api_logger.error)
async def register_face(
    image: UploadFile,
    user_id: int,
    current_user = Depends(auth_manager.get_current_user)
):
    if not current_user.has_permission('register_faces'):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    contents = await image.read()
    frame = cv2.imdecode(
        np.frombuffer(contents, np.uint8),
        cv2.IMREAD_COLOR
    )
    
    encoding = await face_processor.compute_face_encoding(frame)
    await face_processor.store_face_encoding(user_id, encoding)
    
    return {"status": "success"} 
