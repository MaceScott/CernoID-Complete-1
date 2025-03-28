from typing import Dict, Optional, Any, Callable, List, Union
import asyncio
import json
from datetime import datetime
import uuid
from ..base import BaseComponent
from ..utils.decorators import handle_errors

class MessageQueue(BaseComponent):
    """Advanced message queue system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._queues: Dict[str, asyncio.Queue] = {}
        self._handlers: Dict[str, List[Callable]] = {}
        self._subscribers: Dict[str, Dict[str, Callable]] = {}
        self._max_size = self.config.get('queue.max_size', 1000)
        self._retention = self.config.get('queue.retention', 3600)
        self._batch_size = self.config.get('queue.batch_size', 100)
        self._processing_tasks: Dict[str, asyncio.Task] = {}

    async def initialize(self) -> None:
        """Initialize message queue"""
        # Create default queues
        default_queues = ['events', 'notifications', 'tasks']
        for queue in default_queues:
            await self.create_queue(queue)
            
        # Start queue processors
        for queue in self._queues:
            self._start_processor(queue)

    async def cleanup(self) -> None:
        """Cleanup queue resources"""
        # Cancel processing tasks
        for task in self._processing_tasks.values():
            task.cancel()
            
        await asyncio.gather(
            *self._processing_tasks.values(),
            return_exceptions=True
        )
        
        self._queues.clear()
        self._handlers.clear()
        self._subscribers.clear()
        self._processing_tasks.clear()

    @handle_errors(logger=None)
    async def create_queue(self,
                         name: str,
                         max_size: Optional[int] = None) -> None:
        """Create new message queue"""
        if name in self._queues:
            raise ValueError(f"Queue already exists: {name}")
            
        self._queues[name] = asyncio.Queue(
            maxsize=max_size or self._max_size
        )
        self._handlers[name] = []
        self._subscribers[name] = {}
        
        # Start queue processor
        self._start_processor(name)

    @handle_errors(logger=None)
    async def publish(self,
                     queue: str,
                     message: Any,
                     metadata: Optional[Dict] = None) -> str:
        """Publish message to queue"""
        if queue not in self._queues:
            raise ValueError(f"Queue not found: {queue}")
            
        # Create message envelope
        message_id = str(uuid.uuid4())
        envelope = {
            'id': message_id,
            'timestamp': datetime.utcnow().isoformat(),
            'payload': message,
            'metadata': metadata or {}
        }
        
        # Add to queue
        await self._queues[queue].put(envelope)
        
        return message_id

    def subscribe(self,
                 queue: str,
                 callback: Callable,
                 subscriber_id: Optional[str] = None) -> str:
        """Subscribe to queue messages"""
        if queue not in self._queues:
            raise ValueError(f"Queue not found: {queue}")
            
        # Generate subscriber ID if not provided
        subscriber_id = subscriber_id or str(uuid.uuid4())
        
        self._subscribers[queue][subscriber_id] = callback
        return subscriber_id

    def unsubscribe(self,
                    queue: str,
                    subscriber_id: str) -> None:
        """Unsubscribe from queue"""
        if queue in self._subscribers:
            self._subscribers[queue].pop(subscriber_id, None)

    def add_handler(self,
                   queue: str,
                   handler: Callable) -> None:
        """Add message handler to queue"""
        if queue not in self._handlers:
            raise ValueError(f"Queue not found: {queue}")
            
        self._handlers[queue].append(handler)

    async def get_queue_info(self,
                           queue: str) -> Dict[str, Any]:
        """Get queue information"""
        if queue not in self._queues:
            raise ValueError(f"Queue not found: {queue}")
            
        return {
            'name': queue,
            'size': self._queues[queue].qsize(),
            'max_size': self._queues[queue].maxsize,
            'subscribers': len(self._subscribers[queue]),
            'handlers': len(self._handlers[queue])
        }

    def _start_processor(self, queue: str) -> None:
        """Start queue message processor"""
        task = asyncio.create_task(
            self._process_queue(queue)
        )
        self._processing_tasks[queue] = task
        
        # Add cleanup callback
        task.add_done_callback(
            lambda t: self._processing_tasks.pop(queue, None)
        )

    async def _process_queue(self, queue: str) -> None:
        """Process queue messages"""
        while True:
            try:
                # Get message from queue
                message = await self._queues[queue].get()
                
                # Process message
                try:
                    # Run handlers
                    for handler in self._handlers[queue]:
                        try:
                            await handler(message)
                        except Exception as e:
                            self.logger.error(
                                f"Handler failed: {str(e)}"
                            )
                            
                    # Notify subscribers
                    for callback in self._subscribers[queue].values():
                        try:
                            await callback(message)
                        except Exception as e:
                            self.logger.error(
                                f"Subscriber failed: {str(e)}"
                            )
                            
                except Exception as e:
                    self.logger.error(
                        f"Message processing failed: {str(e)}"
                    )
                    
                finally:
                    self._queues[queue].task_done()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(
                    f"Queue processor failed: {str(e)}"
                )
                await asyncio.sleep(1) 