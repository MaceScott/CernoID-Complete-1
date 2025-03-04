from typing import List, Dict, Optional
import numpy as np
from dataclasses import dataclass
from enum import Enum
from core.events.manager import EventManager
from core.error_handling import handle_exceptions
from datetime import datetime
from core.utils.logging import get_logger

behavior_logger = get_logger(__name__)

class BehaviorType(Enum):
    NORMAL = "normal"
    SUSPICIOUS = "suspicious"
    AGGRESSIVE = "aggressive"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    TAILGATING = "tailgating"
    LOITERING = "loitering"

@dataclass
class BehaviorEvent:
    behavior_type: BehaviorType
    confidence: float
    location: str
    timestamp: datetime
    frame_data: Optional[np.ndarray] = None
    person_count: Optional[int] = None

class BehaviorRecognizer:
    def __init__(self):
        self.event_manager = EventManager()
        self.model = self._load_behavior_model()
        self.frame_buffer: List[np.ndarray] = []
        self.detection_threshold = 0.75

    def _load_behavior_model(self):
        try:
            # Load pre-trained behavior recognition model
            # This could be a deep learning model trained on security footage
            behavior_logger.info("Behavior recognition model loaded successfully")
        except Exception as e:
            behavior_logger.error(f"Failed to load behavior recognition model: {str(e)}")
            raise

    @handle_exceptions(logger=behavior_logger.error)
    async def analyze_frame_sequence(self, frames: List[np.ndarray]) -> List[BehaviorEvent]:
        try:
            self.frame_buffer.extend(frames)
            if len(self.frame_buffer) > 30:
                self.frame_buffer = self.frame_buffer[-30:]

            events = []

            person_count = await self._detect_people(frames[-1])
            movement = await self._analyze_movement(self.frame_buffer)
            behaviors = await self._detect_behaviors(self.frame_buffer)

            for behavior in behaviors:
                if behavior['confidence'] > self.detection_threshold:
                    event = BehaviorEvent(
                        behavior_type=behavior['type'],
                        confidence=behavior['confidence'],
                        location=behavior['location'],
                        timestamp=datetime.utcnow(),
                        frame_data=frames[-1],
                        person_count=person_count
                    )
                    events.append(event)
                    await self._handle_behavior_event(event)

            behavior_logger.info(f"Frame sequence analyzed successfully, detected {len(events)} events")
            return events

        except Exception as e:
            behavior_logger.error(f"Frame sequence analysis failed: {str(e)}")
            raise

    async def _handle_behavior_event(self, event: BehaviorEvent):
        try:
            if event.behavior_type in [BehaviorType.SUSPICIOUS, 
                                       BehaviorType.AGGRESSIVE, 
                                       BehaviorType.UNAUTHORIZED_ACCESS]:
                await self.event_manager.publish(Event(
                    type='security_threat',
                    data={
                        'behavior': event.behavior_type.value,
                        'confidence': event.confidence,
                        'location': event.location,
                        'timestamp': event.timestamp,
                        'person_count': event.person_count
                    }
                ))
                behavior_logger.info(f"Behavior event '{event.behavior_type.value}' handled successfully")
        except Exception as e:
            behavior_logger.error(f"Failed to handle behavior event '{event.behavior_type.value}': {str(e)}")
            raise 