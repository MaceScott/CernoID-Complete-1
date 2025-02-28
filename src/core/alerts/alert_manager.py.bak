from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum
from core.events.manager import EventManager
from core.error_handling import handle_exceptions

class AlertPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityAlert:
    id: str
    timestamp: datetime
    priority: AlertPriority
    alert_type: str
    description: str
    camera_id: Optional[int]
    face_data: Optional[Dict]
    location: Optional[str]
    processed: bool = False

class AlertManager:
    def __init__(self):
        self.event_manager = EventManager()
        self.active_alerts: List[SecurityAlert] = []
        self.initialize_handlers()

    @handle_exceptions(logger=alert_logger.error)
    async def initialize_handlers(self):
        await self.event_manager.subscribe('face_detected', self._handle_face_detection)
        await self.event_manager.subscribe('unauthorized_access', self._handle_unauthorized)
        await self.event_manager.subscribe('suspicious_behavior', self._handle_suspicious)

    async def create_alert(self, alert: SecurityAlert):
        self.active_alerts.append(alert)
        await self.event_manager.publish(Event(
            type='new_alert',
            data={'alert': alert}
        ))
        
        if alert.priority in [AlertPriority.HIGH, AlertPriority.CRITICAL]:
            await self._send_immediate_notification(alert)

    async def _handle_face_detection(self, event: Event):
        if not event.data.get('match'):
            await self.create_alert(SecurityAlert(
                id=str(uuid.uuid4()),
                timestamp=datetime.utcnow(),
                priority=AlertPriority.MEDIUM,
                alert_type="unrecognized_face",
                description="Unrecognized person detected",
                camera_id=event.data.get('camera_id'),
                face_data=event.data.get('face_data')
            ))

    async def _send_immediate_notification(self, alert: SecurityAlert):
        # Implementation for immediate notifications (SMS, Email, etc.)
        pass 
