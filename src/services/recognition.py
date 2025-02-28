"""
Face recognition service implementation.
Handles business logic for face recognition operations.
"""

from typing import Optional, List, Dict, Any, Tuple
import numpy as np
from datetime import datetime
from pydantic import BaseModel, EmailStr, ValidationError

from core.recognition.core import FaceRecognitionSystem
from core.utils.errors import handle_errors
from core.database.session import get_db_session
from api.schemas import PersonCreate, PersonResponse, RecognitionResult

# Define a schema for person creation using pydantic
class PersonCreateSchema(BaseModel):
    name: str
    email: EmailStr
    department: Optional[str] = None
    employee_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    face_image: Optional[bytes] = None

# Define a schema for recognition result using pydantic
class RecognitionResultSchema(BaseModel):
    person_id: str
    confidence: float
    matched: bool
    face_location: Tuple[int, int, int, int]
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

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
        try:
            # Validate person data
            validated_data = PersonCreateSchema(**person_data.dict())
        except ValidationError as e:
            self.logger.error(f"Validation error: {e}")
            raise
        
        async with self.db.transaction():
            # Create person record
            person = await self.db.person.create(
                name=validated_data.name,
                email=validated_data.email,
                department=validated_data.department,
                employee_id=validated_data.employee_id,
                metadata=validated_data.metadata
            )
            
            # Process face image if provided
            if validated_data.face_image:
                face_encoding = await self.recognition_system.encode_faces(
                    [validated_data.face_image]
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
        Recognize face in image with enhanced performance and anti-spoofing
        
        Args:
            image_data: Raw image data
            
        Returns:
            Recognition result if face found
        """
        try:
            # Detect and encode face with anti-spoofing
            detections = await self.recognition_system.detect_faces(image_data, check_anti_spoofing=True)
            if not detections:
                self.logger.warning("No faces detected.")
                return None
                
            # Use best detection
            best_detection = max(detections, key=lambda d: d.confidence)
            encodings = await self.recognition_system.encode_faces([best_detection])
            
            if not encodings:
                self.logger.warning("No encodings generated.")
                return None
                
            # Find matches
            matches = await self.recognition_system.find_matches(encodings[0])
            
            if not matches:
                self.logger.info("No matches found.")
                return RecognitionResult(
                    matched=False,
                    confidence=best_detection.confidence,
                    face_location=best_detection.bbox,
                    timestamp=datetime.utcnow()
                )
                
            best_match = matches[0]
            
            # Get person details
            person = await self.db.person.get(best_match.user_id)
            
            result = RecognitionResult(
                person_id=person.id,
                confidence=best_match.confidence,
                matched=True,
                face_location=best_detection.bbox,
                timestamp=datetime.utcnow(),
                metadata=person.metadata
            )
            
            # Validate recognition result
            validated_result = RecognitionResultSchema(**result.dict())
            return validated_result
        except ValidationError as e:
            self.logger.error(f"Validation error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Recognition failed: {str(e)}")
            return None

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