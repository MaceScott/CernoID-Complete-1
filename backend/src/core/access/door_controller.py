"""
Door access control system integration with distance-based activation
"""
from typing import Dict, List, Optional, Tuple
from enum import Enum
import asyncio
import logging
from datetime import datetime
from dataclasses import dataclass

from core.events.manager import EventManager
from core.error_handling import handle_exceptions
from core.monitoring.service import monitoring_service
from core.database.service import Database
from core.security.acl import ACLSystem
from services.notification import NotificationService

logger = logging.getLogger(__name__)

class DoorState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    LOCKED = "locked"
    ERROR = "error"

class DoorType(Enum):
    STANDARD = "standard"
    EMERGENCY = "emergency"
    HIGH_SECURITY = "high_security"
    TURNSTILE = "turnstile"

@dataclass
class DoorConfig:
    door_id: str
    name: str
    type: DoorType
    controller_ip: str
    controller_port: int
    zone_id: int
    emergency_unlock: bool = False
    auto_close_delay: int = 5  # seconds
    requires_confirmation: bool = False
    activation_range: float = 1.5  # meters
    long_range_threshold: float = 6.0  # meters

class DoorController:
    def __init__(self, database: Database, event_manager: EventManager):
        self.database = database
        self.event_manager = event_manager
        self.notification_service = NotificationService()
        self.acl_system = ACLSystem()
        
        # Store door configurations and states
        self.doors: Dict[str, DoorConfig] = {}
        self.door_states: Dict[str, DoorState] = {}
        
        # Connection pool for door controllers
        self.controller_connections: Dict[str, asyncio.Lock] = {}
        
        # Initialize monitoring
        self.monitoring = monitoring_service
        
        # Track user proximity states
        self.user_proximity: Dict[str, Dict[int, float]] = {}  # door_id -> {user_id -> last_distance}
        self.proximity_timeout = 10.0  # seconds
        self._cleanup_task = None

    async def initialize(self):
        """Initialize door controller system"""
        try:
            # Load door configurations from database
            await self._load_door_configs()
            
            # Initialize controller connections
            for door_id, config in self.doors.items():
                self.controller_connections[door_id] = asyncio.Lock()
                self.door_states[door_id] = await self._get_door_state(door_id)
                
            # Start monitoring task
            asyncio.create_task(self._monitor_doors())
            
            # Start proximity cleanup task
            self._cleanup_task = asyncio.create_task(self._cleanup_proximity_data())
            
        except Exception as e:
            logger.error(f"Failed to initialize door controller: {str(e)}")
            raise

    async def _load_door_configs(self):
        """Load door configurations from database"""
        query = "SELECT * FROM door_configs WHERE active = true"
        configs = await self.database.fetch(query)
        
        for config in configs:
            self.doors[config['door_id']] = DoorConfig(
                door_id=config['door_id'],
                name=config['name'],
                type=DoorType(config['type']),
                controller_ip=config['controller_ip'],
                controller_port=config['controller_port'],
                zone_id=config['zone_id'],
                emergency_unlock=config['emergency_unlock'],
                auto_close_delay=config['auto_close_delay'],
                requires_confirmation=config['requires_confirmation']
            )

    async def _cleanup_proximity_data(self):
        """Clean up stale proximity data"""
        while True:
            try:
                current_time = datetime.utcnow().timestamp()
                for door_id in list(self.user_proximity.keys()):
                    for user_id in list(self.user_proximity[door_id].keys()):
                        last_seen = self.user_proximity[door_id][user_id]
                        if current_time - last_seen > self.proximity_timeout:
                            del self.user_proximity[door_id][user_id]
                            
                    if not self.user_proximity[door_id]:
                        del self.user_proximity[door_id]
                        
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in proximity cleanup: {str(e)}")
                await asyncio.sleep(5)

    async def update_user_proximity(self, door_id: str, user_id: int, distance: float):
        """Update user's proximity to a door"""
        if door_id not in self.user_proximity:
            self.user_proximity[door_id] = {}
            
        self.user_proximity[door_id][user_id] = distance
        
        # Trigger events based on proximity
        door_config = self.doors.get(door_id)
        if door_config:
            if distance <= door_config.activation_range:
                await self.event_manager.publish("user_in_activation_range", {
                    "door_id": door_id,
                    "user_id": user_id,
                    "distance": distance
                })
            elif distance <= door_config.long_range_threshold:
                await self.event_manager.publish("user_in_long_range", {
                    "door_id": door_id,
                    "user_id": user_id,
                    "distance": distance
                })

    @handle_exceptions(logger=logger.error)
    async def handle_face_recognition(self, door_id: str, recognition_result: Dict) -> bool:
        """
        Handle face recognition result with distance-based activation
        
        Args:
            door_id: Door identifier
            recognition_result: Recognition result containing match and distance info
            
        Returns:
            True if door was opened
        """
        if not recognition_result or 'match' not in recognition_result:
            return False
            
        match = recognition_result['match']
        distance = recognition_result.get('distance')
        can_activate = recognition_result.get('can_activate', False)
        
        # Update proximity tracking
        if distance is not None:
            await self.update_user_proximity(door_id, match.user_id, distance)
        
        # Check if user is in activation range
        if not can_activate:
            logger.info(f"User {match.user_id} recognized but not in activation range (distance: {distance}m)")
            return False
        
        # Attempt to open door
        return await self.open_door(door_id, match.user_id)

    @handle_exceptions(logger=logger.error)
    async def open_door(self, door_id: str, user_id: int) -> bool:
        """Open door for authorized user within activation range"""
        door_config = self.doors.get(door_id)
        if not door_config:
            logger.error(f"Door {door_id} not found")
            return False
            
        # Check if user is still in activation range
        current_distance = self.user_proximity.get(door_id, {}).get(user_id)
        if current_distance is None or current_distance > door_config.activation_range:
            logger.warning(f"User {user_id} no longer in activation range for door {door_id}")
            return False
            
        # Check access permission
        if not await self.acl_system.check_permission(user_id, f"door_{door_id}", "access"):
            logger.warning(f"Access denied for user {user_id} at door {door_id}")
            await self._handle_access_denied(door_id, user_id)
            return False
            
        try:
            # Get connection lock
            async with self.controller_connections[door_id]:
                # Send open command to door controller
                success = await self._send_door_command(door_id, "open")
                
                if success:
                    # Update door state
                    self.door_states[door_id] = DoorState.OPEN
                    
                    # Schedule auto-close if configured
                    if door_config.auto_close_delay > 0:
                        asyncio.create_task(self._auto_close_door(door_id))
                    
                    # Log access event with distance information
                    await self._log_access_event(
                        door_id, 
                        user_id, 
                        True,
                        {"distance": current_distance}
                    )
                    
                    # Send notification
                    await self._send_access_notification(door_id, user_id, True)
                    
                    return True
                    
                logger.error(f"Failed to open door {door_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error opening door {door_id}: {str(e)}")
            return False

    async def _auto_close_door(self, door_id: str):
        """Automatically close door after delay"""
        door_config = self.doors[door_id]
        await asyncio.sleep(door_config.auto_close_delay)
        await self.close_door(door_id)

    @handle_exceptions(logger=logger.error)
    async def close_door(self, door_id: str) -> bool:
        """Close a door"""
        try:
            async with self.controller_connections[door_id]:
                success = await self._send_door_command(door_id, "close")
                if success:
                    self.door_states[door_id] = DoorState.CLOSED
                return success
        except Exception as e:
            logger.error(f"Error closing door {door_id}: {str(e)}")
            return False

    async def _send_door_command(self, door_id: str, command: str) -> bool:
        """Send command to door controller hardware"""
        door_config = self.doors[door_id]
        try:
            # Implement actual door controller communication here
            # This is a placeholder for the actual hardware integration
            logger.info(f"Sending {command} command to door {door_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send command to door {door_id}: {str(e)}")
            return False

    async def _get_door_state(self, door_id: str) -> DoorState:
        """Get current door state from controller"""
        try:
            # Implement actual door state checking here
            # This is a placeholder for the actual hardware integration
            return DoorState.CLOSED
        except Exception as e:
            logger.error(f"Failed to get door state for {door_id}: {str(e)}")
            return DoorState.ERROR

    async def _monitor_doors(self):
        """Monitor door states and handle events"""
        while True:
            try:
                for door_id in self.doors:
                    current_state = await self._get_door_state(door_id)
                    if current_state != self.door_states[door_id]:
                        await self._handle_state_change(door_id, current_state)
                        self.door_states[door_id] = current_state
                
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Error in door monitoring: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying

    async def _handle_state_change(self, door_id: str, new_state: DoorState):
        """Handle door state changes"""
        await self.event_manager.publish("door_state_changed", {
            "door_id": door_id,
            "state": new_state.value,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Update monitoring metrics
        self.monitoring.update_metric(f"door_{door_id}_state", new_state.value)

    async def _handle_access_denied(self, door_id: str, user_id: int):
        """Handle access denied event"""
        await self.event_manager.publish("access_denied", {
            "door_id": door_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Send notification
        await self._send_access_notification(door_id, user_id, False)

    async def _log_access_event(self, door_id: str, user_id: int, granted: bool, details: Optional[Dict] = None):
        """Log access event to database with additional details"""
        await self.database.execute(
            """
            INSERT INTO access_logs (door_id, user_id, granted, timestamp, details)
            VALUES ($1, $2, $3, $4, $5)
            """,
            door_id, user_id, granted, datetime.utcnow(), details or {}
        )

    async def _send_access_notification(self, door_id: str, user_id: int, granted: bool):
        """Send access notification"""
        door_config = self.doors[door_id]
        user = await self.database.get_user(user_id)
        if user:
            await self.notification_service.send_access_notification(
                person_name=user.name,
                access_point=door_config.name,
                access_type="entry",
                success=granted,
                recipients=await self._get_notification_recipients(door_config.zone_id),
                metadata={
                    "door_id": door_id,
                    "zone_id": door_config.zone_id,
                    "door_type": door_config.type.value
                }
            )

    async def _get_notification_recipients(self, zone_id: int) -> List[str]:
        """Get notification recipients for a zone"""
        query = """
        SELECT DISTINCT email 
        FROM users u 
        JOIN user_notifications un ON u.id = un.user_id 
        WHERE un.zone_id = $1 AND un.notify_access = true
        """
        results = await self.database.fetch(query, zone_id)
        return [r['email'] for r in results]

    async def get_door_status(self, door_id: str) -> Dict:
        """Get door status information"""
        door_config = self.doors.get(door_id)
        if not door_config:
            return {"error": "Door not found"}
            
        return {
            "door_id": door_id,
            "name": door_config.name,
            "state": self.door_states[door_id].value,
            "type": door_config.type.value,
            "zone_id": door_config.zone_id,
            "last_updated": datetime.utcnow().isoformat()
        }

    async def get_zone_door_statuses(self, zone_id: int) -> List[Dict]:
        """Get status of all doors in a zone"""
        return [
            await self.get_door_status(door_id)
            for door_id, config in self.doors.items()
            if config.zone_id == zone_id
        ]

# Global door controller instance
door_controller = DoorController(database=Database(), event_manager=EventManager()) 