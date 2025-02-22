from typing import Dict, List, Optional, Callable, Any, Set
import asyncio
from datetime import datetime
import logging
from dataclasses import dataclass
import json
import aioredis
from collections import defaultdict
from ..base import BaseComponent
from ..connections.redis import RedisPool
from ..utils.errors import handle_errors
import uuid
import time

@dataclass
class Event:
    """Event definition"""
    name: str
    data: Dict
    source: str
    timestamp: datetime
    correlation_id: Optional[str] = None
    metadata: Optional[Dict] = None

class EventDispatcher(BaseComponent):
    """Event dispatching and handling system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._redis: Optional[RedisPool] = None
        self._handlers: Dict[str, List[Callable]] = {}
        self._middleware: List[Callable] = []
        self._history: List[Dict] = []
        self._history_size = self.config.get('events.history_size', 1000)
        self._async_dispatch = self.config.get('events.async_dispatch', True)
        self._subscriptions: Dict[str, asyncio.Task] = {}
        
        # Event configuration
        self._namespace = self.config.get('events.namespace', 'events')
        self._batch_size = self.config.get('events.batch_size', 100)
        self._retention = self.config.get('events.retention', 86400)  # 1 day

    async def initialize(self) -> None:
        """Initialize event dispatcher"""
        self._redis = RedisPool(self.config)
        await self._redis.initialize()
        
        # Start subscription tasks
        for pattern in self._handlers.keys():
            await self._subscribe(pattern)

    async def cleanup(self) -> None:
        """Cleanup event dispatcher resources"""
        # Cancel all subscriptions
        for task in self._subscriptions.values():
            task.cancel()
            
        if self._redis:
            await self._redis.cleanup()
            
        self._handlers.clear()
        self._subscriptions.clear()
        self._middleware.clear()
        self._history.clear()

    def add_handler(self,
                   event: str,
                   handler: Callable) -> None:
        """Add event handler"""
        if event not in self._handlers:
            self._handlers[event] = []
            
        self._handlers[event].append(handler)

    def remove_handler(self,
                      event: str,
                      handler: Callable) -> None:
        """Remove event handler"""
        if event in self._handlers:
            self._handlers[event] = [
                h for h in self._handlers[event]
                if h != handler
            ]

    def add_middleware(self,
                      middleware: Callable) -> None:
        """Add event middleware"""
        self._middleware.append(middleware)

    @handle_errors(logger=None)
    async def dispatch(self,
                      event: str,
                      data: Any = None,
                      metadata: Optional[Dict] = None) -> str:
        """Dispatch event"""
        # Create event object
        event_id = str(uuid.uuid4())
        event_obj = {
            'id': event_id,
            'name': event,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data,
            'metadata': metadata or {}
        }
        
        # Add to history
        self._add_to_history(event_obj)
        
        # Process middleware
        for middleware in self._middleware:
            try:
                event_obj = await middleware(event_obj)
                if not event_obj:
                    return event_id
            except Exception as e:
                self.logger.error(
                    f"Middleware failed: {str(e)}"
                )
                return event_id
                
        # Get handlers
        handlers = self._handlers.get(event, [])
        
        if not handlers:
            return event_id
            
        # Dispatch to handlers
        if self._async_dispatch:
            # Async dispatch
            await asyncio.gather(
                *[
                    self._execute_handler(handler, event_obj)
                    for handler in handlers
                ],
                return_exceptions=True
            )
        else:
            # Sequential dispatch
            for handler in handlers:
                await self._execute_handler(handler, event_obj)
                
        return event_id

    async def subscribe(self,
                       pattern: str,
                       handler: Callable) -> None:
        """Subscribe to events matching pattern"""
        if pattern not in self._handlers:
            self._handlers[pattern] = []
            await self._subscribe(pattern)
            
        self._handlers[pattern].append(handler)

    async def unsubscribe(self,
                         pattern: str,
                         handler: Callable) -> None:
        """Unsubscribe from events"""
        if pattern in self._handlers:
            self._handlers[pattern] = [
                h for h in self._handlers[pattern]
                if h != handler
            ]
            
            if not self._handlers[pattern]:
                # Cancel subscription if no handlers left
                if pattern in self._subscriptions:
                    self._subscriptions[pattern].cancel()
                    del self._subscriptions[pattern]
                del self._handlers[pattern]

    def _make_key(self, key: str) -> str:
        """Create namespaced event key"""
        return f"{self._namespace}:{key}"

    def _generate_id(self) -> str:
        """Generate unique event ID"""
        return str(uuid.uuid4())

    async def _subscribe(self, pattern: str) -> None:
        """Subscribe to Redis channel pattern"""
        pubsub = self._redis.pubsub()
        await pubsub.psubscribe(self._make_key(pattern))
        
        # Start message processing task
        task = asyncio.create_task(
            self._process_messages(pattern, pubsub)
        )
        self._subscriptions[pattern] = task

    async def _process_messages(self,
                              pattern: str,
                              pubsub) -> None:
        """Process incoming messages"""
        try:
            while True:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True
                )
                if message is None:
                    await asyncio.sleep(0.01)
                    continue
                    
                # Process message
                event = json.loads(message['data'])
                await self._handle_event(pattern, event)
                
        except asyncio.CancelledError:
            await pubsub.punsubscribe(pattern)
            await pubsub.close()
        except Exception as e:
            self.logger.error(
                f"Message processing failed: {str(e)}"
            )
            await asyncio.sleep(1)

    async def _handle_event(self,
                          pattern: str,
                          event: Dict) -> None:
        """Handle event with registered handlers"""
        if pattern not in self._handlers:
            return
            
        # Call all handlers
        for handler in self._handlers[pattern]:
            try:
                await handler(event)
            except Exception as e:
                self.logger.error(
                    f"Event handler failed: {str(e)}"
                )

    async def _process_delayed_events(self) -> None:
        """Process delayed events"""
        while True:
            try:
                await asyncio.sleep(1)
                now = int(time.time())
                
                # Get ready events
                events = await self._redis.execute(
                    'zrangebyscore',
                    self._make_key('delayed'),
                    0,
                    now
                )
                
                if not events:
                    continue
                    
                # Process events
                pipe = self._redis.pipeline()
                for event_data in events:
                    data = json.loads(event_data)
                    pipe.publish(
                        data['channel'],
                        json.dumps(data['event'])
                    )
                    pipe.zrem(
                        self._make_key('delayed'),
                        event_data
                    )
                await pipe.execute()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(
                    f"Delayed event processing failed: {str(e)}"
                )
                await asyncio.sleep(1)

    async def get_events(self,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None,
                        event_types: Optional[List[str]] = None) -> List[Event]:
        """Get events within time range"""
        try:
            events = []
            # Get all events from Redis
            event_data = await self._redis.lrange("events", 0, -1)
            
            for data in event_data:
                event_dict = json.loads(data)
                event_time = datetime.fromisoformat(event_dict["timestamp"])
                
                # Apply filters
                if start_time and event_time < start_time:
                    continue
                if end_time and event_time > end_time:
                    continue
                if event_types and event_dict["name"] not in event_types:
                    continue
                    
                events.append(Event(
                    name=event_dict["name"],
                    data=event_dict["data"],
                    source=event_dict["source"],
                    timestamp=event_time,
                    correlation_id=event_dict.get("correlation_id"),
                    metadata=event_dict.get("metadata")
                ))
                
            return events
            
        except Exception as e:
            self.logger.error(f"Event retrieval failed: {str(e)}")
            return []

    async def _process_events(self) -> None:
        """Process events from queue"""
        while self._running:
            try:
                # Get event from Redis
                event_data = await self._redis.brpop("events")
                if not event_data:
                    continue
                    
                event_dict = json.loads(event_data[1])
                event = Event(
                    name=event_dict["name"],
                    data=event_dict["data"],
                    source=event_dict["source"],
                    timestamp=datetime.fromisoformat(event_dict["timestamp"]),
                    correlation_id=event_dict.get("correlation_id"),
                    metadata=event_dict.get("metadata")
                )
                
                # Process event
                handlers = self._handlers.get(event.name, [])
                for handler in handlers:
                    try:
                        await handler(event)
                    except Exception as e:
                        self.logger.error(
                            f"Handler failed for event {event.name}: {str(e)}"
                        )
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Event processing failed: {str(e)}")
                await asyncio.sleep(1)

    async def _cleanup_old_events(self) -> None:
        """Cleanup old events"""
        try:
            retention_days = self.config.get('event_retention_days', 30)
            cutoff_time = datetime.utcnow() - timedelta(days=retention_days)
            
            # Get all events
            events = await self.get_events()
            
            # Remove old events
            for event in events:
                if event.timestamp < cutoff_time:
                    await self._redis.lrem("events", 1, json.dumps({
                        "name": event.name,
                        "data": event.data,
                        "source": event.source,
                        "timestamp": event.timestamp.isoformat(),
                        "correlation_id": event.correlation_id,
                        "metadata": event.metadata
                    }))
                    
        except Exception as e:
            self.logger.error(f"Event cleanup failed: {str(e)}")

    async def get_history(self,
                         event: Optional[str] = None,
                         limit: Optional[int] = None) -> List[Dict]:
        """Get event history"""
        history = self._history
        
        if event:
            history = [
                e for e in history
                if e['name'] == event
            ]
            
        if limit:
            history = history[-limit:]
            
        return history

    def get_handlers(self,
                    event: Optional[str] = None) -> Dict[str, int]:
        """Get registered handlers"""
        if event:
            return {event: len(self._handlers.get(event, []))}
            
        return {
            event: len(handlers)
            for event, handlers in self._handlers.items()
        }

    async def _execute_handler(self,
                             handler: Callable,
                             event: Dict) -> None:
        """Execute event handler"""
        try:
            await handler(event)
        except Exception as e:
            self.logger.error(
                f"Handler failed for {event['name']}: {str(e)}"
            )
            
            # Add error to event history
            event['error'] = str(e)
            self._add_to_history(event)

    def _add_to_history(self, event: Dict) -> None:
        """Add event to history"""
        self._history.append(event)
        
        # Trim history if needed
        if len(self._history) > self._history_size:
            self._history = self._history[-self._history_size:]

    async def _notify_error(self,
                          event: Dict,
                          error: Exception) -> None:
        """Notify error handlers"""
        error_event = {
            'id': str(uuid.uuid4()),
            'name': 'event.error',
            'timestamp': datetime.utcnow().isoformat(),
            'data': {
                'event': event,
                'error': str(error)
            }
        }
        
        await self.dispatch('event.error', error_event) 