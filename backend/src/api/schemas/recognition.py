"""
Face recognition specific schemas.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class FaceDetectionResponse(BaseModel):
    """Response schema for face detection"""
    faces: List[Dict[str, int]] = Field(..., description="List of detected faces with their bounding boxes")
    image_size: Dict[str, int] = Field(..., description="Size of the processed image")
    processing_time: float = Field(..., description="Time taken to process the image")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class FaceEncodingResponse(BaseModel):
    """Response schema for face encoding"""
    encoding: List[float] = Field(..., description="Face encoding vector")
    location: Dict[str, int] = Field(..., description="Face location in the image")
    quality_score: float = Field(..., description="Quality score of the face detection")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class MatchResult(BaseModel):
    """Response schema for face matching"""
    person_id: str = Field(..., description="ID of the matched person")
    confidence_score: float = Field(..., description="Confidence score of the match")
    face_location: Dict[str, int] = Field(..., description="Location of the matched face")
    metadata: Optional[Dict] = Field(default=None, description="Additional metadata about the match")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class RecognitionResult(BaseModel):
    match_found: bool = Field(..., description="Whether a match was found")
    match: Optional[MatchResult] = Field(None, description="Match details if a match was found")
    processing_time: float = Field(..., description="Time taken to process the recognition")
    timestamp: datetime = Field(default_factory=datetime.utcnow) 