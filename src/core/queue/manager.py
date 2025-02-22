from typing import Dict, Optional, Any, List, Union, Callable
import asyncio
import json
import pickle
from datetime import datetime, timedelta
from ..base import BaseComponent
from ..utils.errors import handle_errors

class QueueManager(BaseComponent):
    """Advanced queue management system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._queues: Dict[str, 'Queue'] = {}
        self._consumers: Dict[str, List['Consumer']] = {}
        self._handlers: Dict[str, Dict[str, Callable]] = {}
        self._default_queue = self.config.get('queue.default', 'default')
        self._max_retries = self.config.get('queue.max_retries', 3)
        self._retry_delay = self.config.get('queue.retry_delay', 60)
        self._batch_size = self.config.get('queue.batch_size', 100)
        self._stats = {
            'published': 0,
            'consumed': 0,
            'failed': 0,
            'retried': 0
        }

    async def initialize(self) -> None:
        """Initialize queue manager"""
        # Create default queue
        await self.create_queue(self._default_queue)
        
        # Load queue configurations
        queues = self.config.get('queue.queues', {})
        for name, config in queues.items():
            await self.create_queue(
                name,
                config.get('max_size'),
                config.get('consumers', 1)
            )
            
        # Start cleanup task
        asyncio.create_task(self._cleanup_task())

    async def cleanup(self) -> None:
        """Cleanup queue resources"""
        # Stop all consumers
        for consumers in self._consumers.values():
            for consumer in consumers:
                await consumer.stop()
                
        self._consumers.clear()
        self._queues.clear()
        self._handlers.clear()

    @handle_errors(logger=None)
    async def create_queue(self,
                         name: str,
                         max_size: Optional[int] = None,
                         num_consumers: int = 1) -> 'Queue':
        """Create message queue"""
        try:
            # Create queue
            queue = Queue(
                name,
                max_size or self.config.get('queue.max_size', 0)
            )
            self._queues[name] = queue
            
            # Create consumers
            consumers = []
            for i in range(num_consumers):
                consumer = Consumer(
                    f"{name}-consumer-{i}",
                    queue,
                    self._handlers.get(name, {}),
                    self._max_retries,
                    self._retry_delay,
                    self
                )
                consumers.append(consumer)
                asyncio.create_task(consumer.run())
                
            self._consumers[name] = consumers
            
            return queue
            
        except Exception as e:
            self.logger.error(f"Queue creation error: {str(e)}")
            raise

    @handle_errors(logger=None)
    async def publish(self,
                     message: Any,
                     queue: Optional[str] = None,
                     **kwargs) -> bool:
        """Publish message to queue"""
        try:
            # Get queue
            queue_name = queue or self._default_queue
            if queue_name not in self._queues:
                raise ValueError(f"Unknown queue: {queue_name}")
                
            # Create message
            msg = {
                'id': self._generate_id(),
                'data': message,
                'metadata': kwargs,
                'timestamp': datetime.utcnow().isoformat(),
                'retries': 0
            }
            
            # Add to queue
            await self._queues[queue_name].put(msg)
            
            self._stats['published'] += 1
            
            # Emit event
            await self.app.events.emit(
                'queue.published',
                {
                    'queue': queue_name,
                    'message_id': msg['id']
                }
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Message publish error: {str(e)}")
            return False

    def register_handler(self,
                        queue: str,
                        event: str,
                        handler: Union[Callable, str]) -> None:
        """Register message handler"""
        if queue not in self._handlers:
            self._handlers[queue] = {}
            
        if isinstance(handler, str):
            # Import handler from string
            module_path, func_name = handler.rsplit('.', 1)
            module = importlib.import_module(module_path)
            handler = getattr(module, func_name)
            
        self._handlers[queue][event] = handler

    def remove_handler(self,
                      queue: str,
                      event: str) -> None:
        """Remove message handler"""
        if queue in self._handlers:
            self._handlers[queue].pop(event, None)

    async def get_queue_size(self,
                           queue: Optional[str] = None) -> int:
        """Get queue size"""
        queue_name = queue or self._default_queue
        if queue_name not in self._queues:
            raise ValueError(f"Unknown queue: {queue_name}")
            
        return self._queues[queue_name].qsize()

    async def get_queue_info(self,
                           queue: Optional[str] = None) -> Dict:
        """Get queue information"""
        queue_name = queue or self._default_queue
        if queue_name not in self._queues:
            raise ValueError(f"Unknown queue: {queue_name}")
            
        return {
            'name': queue_name,
            'size': self._queues[queue_name].qsize(),
            'consumers': len(self._consumers[queue_name]),
            'handlers': list(self._handlers.get(queue_name, {}).keys())
        }

    async def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        stats = self._stats.copy()
        stats['queues'] = {
            name: await self.get_queue_info(name)
            for name in self._queues
        }
        return stats

    def _generate_id(self) -> str:
        """Generate unique message ID"""
        import uuid
        return str(uuid.uuid4())

    async def _cleanup_task(self) -> None:
        """Cleanup expired messages"""
        while True:
            try:
                # Cleanup queues
                for queue in self._queues.values():
                    await queue.cleanup()
                    
                await asyncio.sleep(60)  # Run every minute
                
            except Exception as e:
                self.logger.error(f"Queue cleanup error: {str(e)}")
                await asyncio.sleep(60)

    async def _consumer_task(self,
                           queue: str,
                           handler: Callable) -> None:
        """Consumer task"""
        while True:
            try:
                # Get message from queue
                message = await self._backend.get(queue)
                if not message:
                    await asyncio.sleep(1)
                    continue
                    
                # Deserialize message
                try:
                    payload = self._deserialize(message)
                    data = self._deserialize(payload['data'])
                except Exception as e:
                    self.logger.error(
                        f"Message deserialization error: {str(e)}"
                    )
                    continue
                    
                try:
                    # Process message
                    await handler(data)
                    
                    # Acknowledge message
                    await self._backend.ack(queue, message)
                    
                    self._stats['consumed'] += 1
                    
                except Exception as e:
                    self._stats['failed'] += 1
                    
                    # Handle retry
                    retries = payload.get('retries', 0)
                    if retries < self._max_retries:
                        # Update retry count
                        payload['retries'] = retries + 1
                        
                        # Republish with delay
                        delay = self._retry_delay * (retries + 1)
                        await self._backend.publish(
                            queue,
                            self._serialize(payload),
                            delay
                        )
                        
                        self._stats['retried'] += 1
                        
                    else:
                        # Log error
                        self.logger.error(
                            f"Message processing failed: {str(e)}"
                        )
                        
                        # Move to dead letter queue
                        await self._backend.publish(
                            f"{queue}_failed",
                            message
                        )
                        
                    # Acknowledge failed message
                    await self._backend.ack(queue, message)
                    
            except asyncio.CancelledError:
                break
                
            except Exception as e:
                self.logger.error(f"Consumer error: {str(e)}")
                await asyncio.sleep(1)

    def _serialize(self, data: Any) -> Union[str, bytes]:
        """Serialize data"""
        if self._serializer == 'pickle':
            return pickle.dumps(data)
        else:
            return json.dumps(data)

    def _deserialize(self, data: Union[str, bytes]) -> Any:
        """Deserialize data"""
        if self._serializer == 'pickle':
            return pickle.loads(data)
        else:
            return json.loads(data) 