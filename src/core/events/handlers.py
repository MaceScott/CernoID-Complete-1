from typing import Dict, Any
from .event_bus import Event

class EventHandler:
    """Base class for event handlers"""
    
    async def handle(self, event: Event) -> None:
        handler_method = getattr(self, f"handle_{event.type}", None)
        if handler_method:
            await handler_method(event.data)
        else:
            raise NotImplementedError(f"Handler not implemented for {event.type}")
            
class RecognitionEventHandler(EventHandler):
    async def handle_face_detected(self, data: Dict[str, Any]) -> None:
        # Handle face detection event
        pass
        
    async def handle_person_identified(self, data: Dict[str, Any]) -> None:
        # Handle person identification event
        pass 