from typing import Dict, Optional, Any, List, Union, Callable, Set
import asyncio
import inspect
from datetime import datetime
from ..base import BaseComponent
from ..utils.decorators import handle_errors
from ..logging import get_logger

logger = get_logger(__name__)

class EventManager(BaseComponent):
    """Manages system events and their handlers."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            # Initialize with empty config, will be updated in initialize()
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Only initialize if not already initialized
        if not hasattr(self, '_initialized'):
            # Initialize with empty config, will be updated in initialize()
            super().__init__({})
            self._initialized = False
            self._handlers: Dict[str, List[Callable]] = {}
            self._event_queue = asyncio.Queue()
            self._processing = False
            self._wildcards: Set[Callable] = set()
            self._middleware: List[Callable] = []
            self._stats = {
                'emitted': 0,
                'handled': 0,
                'errors': 0
            }

    @handle_errors
    async def initialize(self) -> None:
        """Initialize the event manager."""
        if not self._initialized:
            # Import settings here to avoid circular imports
            from ..config import settings
            
            # Update config with actual settings
            self.config = settings.dict()
            
            # Initialize settings-dependent attributes
            self._max_listeners = self.config.get('events.max_listeners', 100)
            self._propagate_errors = self.config.get('events.propagate_errors', False)
            self._async_dispatch = self.config.get('events.async_dispatch', True)
            self._queue_size = self.config.get('events.queue_size', 1000)
            
            self._processing = True
            asyncio.create_task(self._process_events())
            self._initialized = True
            logger.info("Event manager initialized successfully")

    @handle_errors
    async def cleanup(self) -> None:
        """Clean up event manager resources."""
        self._processing = False
        await self._event_queue.put(None)  # Signal to stop processing
        self._handlers.clear()
        self._wildcards.clear()
        self._middleware.clear()

    @handle_errors
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe to an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        
    @handle_errors
    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Unsubscribe from an event type."""
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)
            
    @handle_errors
    async def emit(self, event_type: str, data: Any = None) -> None:
        """Emit an event."""
        event = {
            'type': event_type,
            'data': data,
            'timestamp': datetime.utcnow()
        }
        await self._event_queue.put(event)
        
    async def _process_events(self) -> None:
        """Process events from the queue."""
        while self._processing:
            event = await self._event_queue.get()
            if event is None:  # Stop signal
                break
                
            event_type = event['type']
            if event_type in self._handlers:
                for handler in self._handlers[event_type]:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(event)
                        else:
                            handler(event)
                    except Exception as e:
                        logger.error(f"Error processing event {event_type}: {e}")
                        
            self._event_queue.task_done()

    @handle_errors
    def on(self,
          event: str,
          handler: Callable,
          priority: int = 0) -> None:
        """Register event handler"""
        # Validate handler
        if not callable(handler):
            raise ValueError("Handler must be callable")
            
        # Check max listeners
        total_handlers = sum(len(h) for h in self._handlers.values())
        if total_handlers >= self._max_listeners:
            raise ValueError("Maximum number of listeners reached")
            
        # Handle wildcard events
        if event == '*':
            self._wildcards.add(handler)
            return
            
        # Initialize handler set if needed
        if event not in self._handlers:
            self._handlers[event] = []
            
        # Add handler
        self._handlers[event].append(handler)

    @handle_errors
    def off(self,
            event: str,
            handler: Optional[Callable] = None) -> None:
        """Remove event handler"""
        if event == '*':
            if handler:
                self._wildcards.discard(handler)
            else:
                self._wildcards.clear()
            return
            
        if event not in self._handlers:
            return
            
        if handler:
            self._handlers[event].remove(handler)
            if not self._handlers[event]:
                del self._handlers[event]
        else:
            del self._handlers[event]

    @handle_errors
    def use(self, middleware: Callable) -> None:
        """Add event middleware"""
        if not callable(middleware):
            raise ValueError("Middleware must be callable")
        self._middleware.append(middleware)

    @handle_errors
    async def emit_event(self,
                  event: Dict,
                  wait: bool = False) -> None:
        """Emit event"""
        try:
            # Create event object
            evt = Event(event['type'], event['data'])
            
            # Apply middleware
            for middleware in self._middleware:
                if inspect.iscoroutinefunction(middleware):
                    evt = await middleware(evt)
                else:
                    evt = middleware(evt)
                    
                if evt is None:
                    return
                    
            # Handle async dispatch
            if self._async_dispatch and not wait:
                await self._event_queue.put(evt)
                self._stats['emitted'] += 1
                return
                
            # Dispatch event
            await self._dispatch_event(evt)
            self._stats['emitted'] += 1
            
        except Exception as e:
            logger.error(f"Event emission error: {str(e)}")
            self._stats['errors'] += 1
            if self._propagate_errors:
                raise

    @handle_errors
    async def emit_many(self,
                       events: List[Dict],
                       wait: bool = False) -> None:
        """Emit multiple events"""
        for event_data in events:
            await self.emit_event(event_data, wait)

    @handle_errors
    def once(self,
             event: str,
             handler: Callable) -> None:
        """Register one-time event handler"""
        async def wrapper(*args, **kwargs):
            self.off(event, wrapper)
            if inspect.iscoroutinefunction(handler):
                await handler(*args, **kwargs)
            else:
                handler(*args, **kwargs)
                
        self.on(event, wrapper)

    @handle_errors
    async def get_stats(self) -> Dict[str, Any]:
        """Get event statistics"""
        return self._stats.copy()

    async def _dispatch_event(self, event: 'Event') -> None:
        """Dispatch event to handlers"""
        try:
            # Get handlers for event
            handlers = self._handlers.get(event.name, [])
            
            # Add wildcard handlers
            handlers.extend(self._wildcards)
            
            if not handlers:
                return
                
            # Call handlers
            for handler in handlers:
                try:
                    if inspect.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                        
                    self._stats['handled'] += 1
                    
                except Exception as e:
                    logger.error(
                        f"Event handler error: {str(e)}"
                    )
                    self._stats['errors'] += 1
                    if self._propagate_errors:
                        raise
                        
        except Exception as e:
            logger.error(f"Event dispatch error: {str(e)}")
            self._stats['errors'] += 1
            if self._propagate_errors:
                raise

# Create singleton instance
event_manager = EventManager()

class Event:
    """Event object"""
    
    def __init__(self,
                 name: str,
                 data: Optional[Any] = None):
        self.name = name
        self.data = data
        self.timestamp = datetime.utcnow()
        self.propagation_stopped = False

    def stop_propagation(self) -> None:
        """Stop event propagation"""
        self.propagation_stopped = True 