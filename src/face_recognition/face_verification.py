from typing import Optional, Dict
import numpy as np
from core.events.manager import EventManager
from core.error_handling import handle_exceptions

class FaceVerifier:
    def __init__(self):
        self.event_manager = EventManager()
        self.encoder = FaceEncoder()
        self.matcher = FaceMatcher()

    @handle_exceptions(logger=verification_logger.error)
    async def verify_face(self, face_image: np.ndarray) -> Optional[Dict]:
        encoding = await self.encoder.encode_faces([face_image])[0]
        matches = await self.matcher.find_matches(encoding)
        
        if matches:
            best_match = matches[0]
            await self.event_manager.publish(Event(
                type='face_verified',
                data={'match': best_match}
            ))
            return best_match
        
        await self.event_manager.publish(Event(
            type='face_unverified',
            data={'face_encoding': encoding}
        ))
        return None 
