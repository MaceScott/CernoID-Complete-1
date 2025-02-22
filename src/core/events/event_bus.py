from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from datetime import datetime
import asyncio
import json

@dataclass
class Event:
    """Event data structure"""
    type: str
    data: Dict[str, Any]
    timestamp: datetime = datetime.now()
    
    def to_json(self) -> str:
        """Convert event to JSON string"""
        return json.dumps({
            'type': self.type,
            'data': self.data,
            'timestamp': self.timestamp.isoformat()
        })

class EventBus:
    """Event management and distribution system"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.logger = self._setup_logger()
        self._running = False
        self._queue = asyncio.Queue()
        self._tasks: List[asyncio.Task] = []

    async def start(self) -> None:
        """Start event processing"""
        if self._running:
            return
            
        self._running = True
        self._tasks.append(
            asyncio.create_task(self._process_events())
        )
        self.logger.info("Event bus started")

    async def stop(self) -> None:
        """Stop event processing"""
        self._running = False
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
            
        # Wait for tasks to complete
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        
        self.logger.info("Event bus stopped")

    async def publish(self, event: Event) -> None:
        """Publish an event"""
        await self._queue.put(event)
        self.logger.debug(f"Event queued: {event.type}")

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe to an event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)
        self.logger.debug(f"Handler subscribed to {event_type}")

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Unsubscribe from an event type"""
        if event_type in self.subscribers and handler in self.subscribers[event_type]:
            self.subscribers[event_type].remove(handler)
            self.logger.debug(f"Handler unsubscribed from {event_type}")

    async def _process_events(self) -> None:
        """Process events from queue"""
        while self._running:
            try:
                event = await self._queue.get()
                await self._handle_event(event)
                self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Event processing error: {str(e)}")

    async def _handle_event(self, event: Event) -> None:
        """Handle a single event"""
        handlers = self.subscribers.get(event.type, [])
        
        if not handlers:
            self.logger.warning(f"No handlers for event type: {event.type}")
            return

        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                self.logger.error(
                    f"Handler {handler.__name__} failed for {event.type}: {str(e)}"
                )

    def _setup_logger(self):
        """Setup event bus logger"""
        from core.logging import LogManager
        return LogManager().get_logger("EventBus") 