from typing import Dict, Optional, Any, List, Union, Callable, Set
import asyncio
import inspect
from datetime import datetime
from ..base import BaseComponent
from ..utils.errors import handle_errors

class EventManager(BaseComponent):
    """Advanced event management system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._handlers: Dict[str, Set[Callable]] = {}
        self._wildcards: Set[Callable] = set()
        self._middleware: List[Callable] = []
        self._max_listeners = self.config.get('events.max_listeners', 100)
        self._propagate_errors = self.config.get('events.propagate_errors', False)
        self._async_dispatch = self.config.get('events.async_dispatch', True)
        self._queue_size = self.config.get('events.queue_size', 1000)
        self._stats = {
            'emitted': 0,
            'handled': 0,
            'errors': 0
        }

    async def initialize(self) -> None:
        """Initialize event manager"""
        # Initialize event queue if async dispatch enabled
        if self._async_dispatch:
            self._queue = asyncio.Queue(maxsize=self._queue_size)
            asyncio.create_task(self._dispatch_task())

    async def cleanup(self) -> None:
        """Cleanup event resources"""
        self._handlers.clear()
        self._wildcards.clear()
        self._middleware.clear()

    @handle_errors(logger=None)
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
            self._handlers[event] = set()
            
        # Add handler
        self._handlers[event].add(handler)

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
            self._handlers[event].discard(handler)
            if not self._handlers[event]:
                del self._handlers[event]
        else:
            del self._handlers[event]

    def use(self, middleware: Callable) -> None:
        """Add event middleware"""
        if not callable(middleware):
            raise ValueError("Middleware must be callable")
        self._middleware.append(middleware)

    @handle_errors(logger=None)
    async def emit(self,
                  event: str,
                  data: Optional[Any] = None,
                  wait: bool = False) -> None:
        """Emit event"""
        try:
            # Create event object
            evt = Event(event, data)
            
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
                await self._queue.put(evt)
                self._stats['emitted'] += 1
                return
                
            # Dispatch event
            await self._dispatch_event(evt)
            self._stats['emitted'] += 1
            
        except Exception as e:
            self.logger.error(f"Event emission error: {str(e)}")
            self._stats['errors'] += 1
            if self._propagate_errors:
                raise

    async def emit_many(self,
                       events: List[Dict],
                       wait: bool = False) -> None:
        """Emit multiple events"""
        for event_data in events:
            await self.emit(
                event_data['event'],
                event_data.get('data'),
                wait
            )

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

    async def get_stats(self) -> Dict[str, Any]:
        """Get event statistics"""
        return self._stats.copy()

    async def _dispatch_event(self, event: 'Event') -> None:
        """Dispatch event to handlers"""
        try:
            # Get handlers for event
            handlers = self._handlers.get(event.name, set())
            
            # Add wildcard handlers
            handlers.update(self._wildcards)
            
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
                    self.logger.error(
                        f"Event handler error: {str(e)}"
                    )
                    self._stats['errors'] += 1
                    if self._propagate_errors:
                        raise
                        
        except Exception as e:
            self.logger.error(f"Event dispatch error: {str(e)}")
            self._stats['errors'] += 1
            if self._propagate_errors:
                raise

    async def _dispatch_task(self) -> None:
        """Async event dispatch task"""
        while True:
            try:
                # Get event from queue
                event = await self._queue.get()
                
                # Dispatch event
                await self._dispatch_event(event)
                
                # Mark task as done
                self._queue.task_done()
                
            except Exception as e:
                self.logger.error(
                    f"Event dispatch task error: {str(e)}"
                )
                self._stats['errors'] += 1


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