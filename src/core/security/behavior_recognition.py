from typing import List, Dict, Optional
import numpy as np
from dataclasses import dataclass
from enum import Enum
from core.events.manager import EventManager
from core.error_handling import handle_exceptions

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
        # Load pre-trained behavior recognition model
        # This could be a deep learning model trained on security footage
        pass

    @handle_exceptions(logger=behavior_logger.error)
    async def analyze_frame_sequence(self, frames: List[np.ndarray]) -> List[BehaviorEvent]:
        self.frame_buffer.extend(frames)
        if len(self.frame_buffer) > 30:  # Analyze last 30 frames
            self.frame_buffer = self.frame_buffer[-30:]

        events = []
        
        # Detect number of people
        person_count = await self._detect_people(frames[-1])
        
        # Analyze movement patterns
        movement = await self._analyze_movement(self.frame_buffer)
        
        # Detect specific behaviors
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

        return events

    async def _handle_behavior_event(self, event: BehaviorEvent):
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
