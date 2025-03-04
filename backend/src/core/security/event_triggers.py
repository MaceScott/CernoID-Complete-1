from typing import Dict, Any, Callable, List
from dataclasses import dataclass
from datetime import datetime
from core.events.manager import EventManager
from core.error_handling import handle_exceptions
from core.utils.logging import get_logger

security_logger = get_logger(__name__)

@dataclass
class SecurityTrigger:
    name: str
    conditions: Dict[str, Any]
    action: Callable
    priority: int
    enabled: bool = True

class SecurityEventTrigger:
    def __init__(self):
        self.event_manager = EventManager()
        self.triggers: Dict[str, SecurityTrigger] = {}
        self.initialize_default_triggers()
        
    @handle_exceptions(logger=security_logger.error)
    def initialize_default_triggers(self):
        # Add default security triggers
        self.add_trigger(
            SecurityTrigger(
                name="multiple_unauthorized_access",
                conditions={
                    "event_type": "unauthorized_access",
                    "count_threshold": 3,
                    "time_window": 300  # 5 minutes
                },
                action=self._handle_multiple_unauthorized,
                priority=1
            )
        )
        
        self.add_trigger(
            SecurityTrigger(
                name="suspicious_after_hours",
                conditions={
                    "event_type": "movement_detected",
                    "time_range": {"start": "18:00", "end": "06:00"}
                },
                action=self._handle_after_hours,
                priority=2
            )
        )

    async def process_event(self, event: Dict):
        try:
            triggered_actions = 0
            for trigger in self.triggers.values():
                if trigger.enabled and self._check_conditions(event, trigger.conditions):
                    await trigger.action(event)
                    triggered_actions += 1

            security_logger.info(f"Event processed successfully: {event}, triggered {triggered_actions} actions")
        except Exception as e:
            security_logger.error(f"Event processing failed: {str(e)}")
            raise

    def _check_conditions(self, event: Dict, conditions: Dict) -> bool:
        for key, value in conditions.items():
            if key == "time_range":
                if not self._check_time_range(value):
                    return False
            elif key == "count_threshold":
                if not self._check_threshold(event, value):
                    return False
            elif event.get(key) != value:
                return False
        return True

    async def _handle_multiple_unauthorized(self, event: Dict):
        await self.event_manager.publish(Event(
            type='security_breach',
            data={
                'trigger': 'multiple_unauthorized_access',
                'details': event,
                'timestamp': datetime.utcnow()
            }
        ))

    async def _handle_after_hours(self, event: Dict):
        await self.event_manager.publish(Event(
            type='suspicious_activity',
            data={
                'trigger': 'after_hours_movement',
                'details': event,
                'timestamp': datetime.utcnow()
            }
        )) 
