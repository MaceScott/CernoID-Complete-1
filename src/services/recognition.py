"""
Face recognition service implementation.
Handles business logic for face recognition operations.
"""

from typing import Optional, List, Dict, Any
import numpy as np
from datetime import datetime

from core.recognition.core import FaceRecognitionSystem
from core.utils.errors import handle_errors
from core.database.session import get_db_session
from api.schemas import PersonCreate, PersonResponse, RecognitionResult

class RecognitionService:
    def __init__(self):
        self.recognition_system = FaceRecognitionSystem()
        self.db = get_db_session()

    @handle_errors
    async def create_person(self, person_data: PersonCreate) -> PersonResponse:
        """
        Create a new person with face data
        
        Args:
            person_data: Person information and face image
            
        Returns:
            Created person details
        """
        async with self.db.transaction():
            # Create person record
            person = await self.db.person.create(
                name=person_data.name,
                email=person_data.email,
                department=person_data.department,
                employee_id=person_data.employee_id,
                metadata=person_data.metadata
            )
            
            # Process face image if provided
            if person_data.face_image:
                face_encoding = await self.recognition_system.encode_faces(
                    [person_data.face_image]
                )[0]
                
                # Store face encoding
                await self.db.face_encoding.create(
                    person_id=person.id,
                    encoding_data=face_encoding
                )
            
            return PersonResponse.from_orm(person)

    @handle_errors
    async def recognize_face(self, image_data: bytes) -> Optional[RecognitionResult]:
        """
        Recognize face in image
        
        Args:
            image_data: Raw image data
            
        Returns:
            Recognition result if face found
        """
        # Detect and encode face
        detections = await self.recognition_system.detect_faces(image_data)
        if not detections:
            return None
            
        # Use best detection
        best_detection = max(detections, key=lambda d: d.confidence)
        encodings = await self.recognition_system.encode_faces([best_detection])
        
        if not encodings:
            return None
            
        # Find matches
        matches = await self.recognition_system.find_matches(encodings[0])
        
        if not matches:
            return RecognitionResult(
                matched=False,
                confidence=best_detection.confidence,
                face_location=best_detection.bbox,
                timestamp=datetime.utcnow()
            )
            
        best_match = matches[0]
        
        # Get person details
        person = await self.db.person.get(best_match.user_id)
        
        return RecognitionResult(
            person_id=person.id,
            confidence=best_match.confidence,
            matched=True,
            face_location=best_detection.bbox,
            timestamp=datetime.utcnow(),
            metadata=person.metadata
        )

    @handle_errors
    async def update_person(self, 
                          person_id: int, 
                          face_image: Optional[bytes] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> PersonResponse:
        """
        Update person's face data or metadata
        
        Args:
            person_id: Person ID to update
            face_image: Optional new face image
            metadata: Optional metadata updates
            
        Returns:
            Updated person details
        """
        async with self.db.transaction():
            person = await self.db.person.get(person_id)
            if not person:
                raise ValueError(f"Person {person_id} not found")
                
            if face_image:
                # Generate new encoding
                face_encoding = await self.recognition_system.encode_faces(
                    [face_image]
                )[0]
                
                # Update face encoding
                await self.db.face_encoding.update(
                    person_id=person_id,
                    encoding_data=face_encoding
                )
                
            if metadata:
                # Update metadata
                person.metadata.update(metadata)
                await self.db.person.update(
                    person_id=person_id,
                    metadata=person.metadata
                )
                
            return PersonResponse.from_orm(person)

    @handle_errors
    async def delete_person(self, person_id: int) -> bool:
        """
        Delete person and associated face data
        
        Args:
            person_id: Person ID to delete
            
        Returns:
            True if successful
        """
        async with self.db.transaction():
            # Delete face encodings first
            await self.db.face_encoding.delete(person_id=person_id)
            # Delete person record
            await self.db.person.delete(id=person_id)
            return True 