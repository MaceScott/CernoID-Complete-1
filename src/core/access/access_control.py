from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum
from dataclasses import dataclass
from core.error_handling import handle_exceptions
from core.events.manager import EventManager

class AccessLevel(Enum):
    NONE = 0
    BASIC = 1
    RESTRICTED = 2
    HIGH_SECURITY = 3
    ADMIN = 4

@dataclass
class AccessZone:
    id: int
    name: str
    required_level: AccessLevel
    door_controllers: List[str]
    schedule: Optional[Dict] = None  # Time-based access restrictions

class AccessController:
    def __init__(self):
        self.event_manager = EventManager()
        self.zones: Dict[int, AccessZone] = {}
        self.user_permissions: Dict[int, Dict[int, AccessLevel]] = {}  # user_id -> {zone_id -> level}

    @handle_exceptions(logger=access_logger.error)
    async def grant_access(self, user_id: int, zone_id: int, level: AccessLevel):
        if user_id not in self.user_permissions:
            self.user_permissions[user_id] = {}
        
        self.user_permissions[user_id][zone_id] = level
        await self.event_manager.publish(Event(
            type='access_granted',
            data={
                'user_id': user_id,
                'zone_id': zone_id,
                'level': level.value
            }
        ))

    async def check_access(self, user_id: int, zone_id: int) -> bool:
        zone = self.zones.get(zone_id)
        if not zone:
            return False

        user_level = self.user_permissions.get(user_id, {}).get(zone_id, AccessLevel.NONE)
        
        if user_level.value < zone.required_level.value:
            await self._log_access_denied(user_id, zone_id)
            return False

        if zone.schedule and not self._check_schedule(zone.schedule):
            await self._log_schedule_violation(user_id, zone_id)
            return False

        return True

    def _check_schedule(self, schedule: Dict) -> bool:
        current_time = datetime.now().time()
        current_day = datetime.now().strftime('%A').lower()
        
        if current_day not in schedule:
            return False
            
        for time_range in schedule[current_day]:
            start = datetime.strptime(time_range['start'], '%H:%M').time()
            end = datetime.strptime(time_range['end'], '%H:%M').time()
            if start <= current_time <= end:
                return True
                
        return False 
