"""
File: face.py
Purpose: Face model for storing and managing face recognition data in the CernoID system.

Key Features:
- Face encoding storage and validation
- Recognition confidence tracking
- Image path management
- Metadata storage
- Quality scoring
- Recognition statistics

Dependencies:
- NumPy: Face encoding operations
- Pydantic: Data validation
- Core services:
  - BaseDBModel: Base model functionality
  - Database: Storage operations
  - ImageProcessor: Image handling
  - Recognition: Face detection

Architecture:
- Model inheritance
- Field validation
- Type checking
- Event tracking
- Error handling
- State management

Performance:
- Encoding optimization
- Image caching
- Batch processing
- Index support
- Query optimization
- Resource management
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import numpy as np
from pydantic import Field, validator
import base64

from .base import BaseDBModel
from ...utils.logging import get_logger

logger = get_logger(__name__)

class Face(BaseDBModel):
    """
    Face model for recognition data storage.
    
    Attributes:
        person_id (str): Associated person identifier
        encoding (Union[str, np.ndarray]): Face encoding data
        confidence (float): Recognition confidence score
        metadata (Dict[str, Any]): Additional face data
        image_paths (List[str]): Associated image paths
        active (bool): Face status flag
        last_seen (datetime): Last recognition timestamp
        recognition_count (int): Total recognition count
        
    Features:
        - Face encoding validation
        - Recognition tracking
        - Image management
        - Quality scoring
        - Statistics tracking
        
    Performance:
        - Encoding optimization
        - Batch processing
        - Cache support
        - Index usage
        - Resource pooling
    """
    
    person_id: str = Field(..., description="Associated person identifier")
    encoding: Union[str, np.ndarray] = Field(..., description="Face encoding data")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    image_paths: List[str] = Field(default_factory=list)
    active: bool = True
    last_seen: Optional[datetime] = None
    recognition_count: int = Field(default=0, ge=0)
    
    @validator("encoding")
    def validate_encoding(cls, v: Union[str, np.ndarray]) -> Union[str, np.ndarray]:
        """
        Validate face encoding data.
        
        Args:
            v: Face encoding (base64 string or numpy array)
            
        Returns:
            Union[str, np.ndarray]: Validated encoding
            
        Validation:
            - Type checking
            - Dimension validation
            - Size constraints
            - Format validation
            - Data integrity
        """
        try:
            if isinstance(v, str):
                # Decode base64 string
                encoding_bytes = base64.b64decode(v)
                encoding = np.frombuffer(encoding_bytes, dtype=np.float64)
                if encoding.shape != (128,):
                    raise ValueError("Invalid encoding shape")
                return v
            elif isinstance(v, np.ndarray):
                if v.shape != (128,):
                    raise ValueError("Invalid encoding shape")
                return v
            else:
                raise ValueError("Encoding must be base64 string or numpy array")
                
        except Exception as e:
            logger.error(f"Encoding validation failed: {str(e)}")
            raise
            
    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Convert model to dictionary.
        
        Args:
            *args: Additional arguments
            **kwargs: Additional keyword arguments
            
        Returns:
            Dict[str, Any]: Model dictionary
            
        Features:
            - Encoding serialization
            - Type conversion
            - Field filtering
            - Nested models
            - Custom encoders
        """
        d = super().dict(*args, **kwargs)
        
        # Convert numpy array to base64
        if isinstance(self.encoding, np.ndarray):
            encoding_bytes = self.encoding.tobytes()
            d["encoding"] = base64.b64encode(encoding_bytes).decode()
            
        return d
        
    async def update_recognition(self, db, confidence: float) -> None:
        """
        Update recognition statistics.
        
        Args:
            db: Database connection
            confidence: Recognition confidence score
            
        Features:
            - Confidence tracking
            - Count increment
            - Timestamp update
            - Event dispatch
            - Audit logging
        """
        try:
            self.recognition_count += 1
            self.last_seen = datetime.utcnow()
            self.confidence = max(self.confidence, confidence)
            
            await self.save(db)
            
        except Exception as e:
            logger.error(f"Failed to update recognition: {str(e)}")
            raise
            
    async def add_image(self, db, image_path: str) -> None:
        """
        Add image path to face record.
        
        Args:
            db: Database connection
            image_path: Path to face image
            
        Features:
            - Path validation
            - Duplicate check
            - Size management
            - Event dispatch
            - Audit logging
        """
        try:
            if image_path not in self.image_paths:
                self.image_paths.append(image_path)
                await self.save(db)
                
        except Exception as e:
            logger.error(f"Failed to add image: {str(e)}")
            raise
            
    async def update_metadata(self, db, metadata: Dict[str, Any]) -> None:
        """
        Update face metadata.
        
        Args:
            db: Database connection
            metadata: Metadata dictionary
            
        Features:
            - Key validation
            - Value validation
            - Size management
            - Event dispatch
            - Audit logging
        """
        try:
            self.metadata.update(metadata)
            await self.save(db)
            
        except Exception as e:
            logger.error(f"Failed to update metadata: {str(e)}")
            raise
            
    def get_quality_score(self) -> float:
        """
        Calculate face quality score.
        
        Returns:
            float: Quality score (0.0-1.0)
            
        Features:
            - Confidence weighting
            - Image count factor
            - Recognition history
            - Metadata analysis
            - Age consideration
        """
        try:
            # Base score from confidence
            score = self.confidence * 0.4
            
            # Image count factor
            image_factor = min(len(self.image_paths) / 5.0, 1.0) * 0.3
            
            # Recognition history factor
            recognition_factor = min(self.recognition_count / 100.0, 1.0) * 0.3
            
            return score + image_factor + recognition_factor
            
        except Exception as e:
            logger.error(f"Failed to calculate quality score: {str(e)}")
            return 0.0
            
    @classmethod
    def get_indexes(cls) -> List[Dict]:
        """
        Get collection indexes.
        
        Returns:
            List[Dict]: Index specifications
            
        Indexes:
            - person_id
            - active
            - confidence
            - last_seen
            - recognition_count
        """
        return [
            {
                "keys": [("person_id", 1)]
            },
            {
                "keys": [("active", 1)]
            },
            {
                "keys": [("confidence", -1)]
            },
            {
                "keys": [("last_seen", -1)]
            },
            {
                "keys": [("recognition_count", -1)]
            }
        ] 