from typing import Dict, Optional, List, Union
import numpy as np
from pydantic import validator
from .base import BaseDBModel

class Face(BaseDBModel):
    """Face model"""
    
    person_id: str
    encoding: Union[str, np.ndarray]  # Base64 encoded or numpy array
    confidence: float
    metadata: Dict
    image_paths: List[str]
    active: bool = True
    last_seen: Optional[datetime]
    recognition_count: int = 0
    
    @validator('encoding')
    def validate_encoding(cls, v):
        """Validate face encoding"""
        if isinstance(v, str):
            # Convert base64 to numpy array
            import base64
            encoding = np.frombuffer(
                base64.b64decode(v),
                dtype=np.float64
            )
            return encoding.reshape(-1)
        return v

    def dict(self, *args, **kwargs) -> Dict:
        """Convert model to dictionary"""
        d = super().dict(*args, **kwargs)
        # Convert numpy array to base64
        if isinstance(d['encoding'], np.ndarray):
            import base64
            d['encoding'] = base64.b64encode(
                d['encoding'].tobytes()
            ).decode('utf-8')
        return d

    async def update_recognition(self, db) -> None:
        """Update recognition statistics"""
        await db.faces.update_one(
            {'id': self.id},
            {
                '$set': {
                    'last_seen': datetime.utcnow(),
                    'recognition_count': self.recognition_count + 1
                }
            }
        ) 