from typing import Dict, List, Optional, Callable, Any
import asyncio
import json
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import aio_pika
import backoff
from functools import wraps

@dataclass
class TaskConfig:
    """Task configuration"""
    name: str
    queue: str
    retry_limit: int = 3
    retry_delay: int = 60
    timeout: int = 300
    priority: int = 0
    dead_letter_queue: Optional[str] = None

class TaskQueue:
    """Distributed task queue system"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger('TaskQueue')
        self._connection: Optional[aio_pika.Connection] = None
        self._channel: Optional[aio_pika.Channel] = None
        self._queues: Dict[str, aio_pika.Queue] = {}
        self._handlers: Dict[str, Callable] = {}
        self._tasks: Dict[str, asyncio.Task] = {}
        self._processing: Dict[str, int] = {}

    async def initialize(self) -> None:
        """Initialize task queue"""
        try:
            # Connect to RabbitMQ
            self._connection = await aio_pika.connect_robust(
                self.config['rabbitmq_url']
            )
            
            # Create channel
            self._channel = await self._connection.channel()
            await self._channel.set_qos(prefetch_count=10)
            
            # Setup queues
            await self._setup_queues()
            
            self.logger.info("Task queue initialized")
            
        except Exception as e:
            self.logger.error(f"Task queue initialization failed: {str(e)}")
            raise

    async def cleanup(self) -> None:
        """Cleanup task queue resources"""
        try:
            # Cancel running tasks
            for task in self._tasks.values():
                task.cancel()
                
            # Close channel and connection
            if self._channel:
                await self._channel.close()
            if self._connection:
                await self._connection.close()
                
            self.logger.info("Task queue cleaned up")
            
        except Exception as e:
            self.logger.error(f"Task queue cleanup failed: {str(e)}")

    async def enqueue(self,
                     task_name: str,
                     payload: Dict,
                     priority: Optional[int] = None) -> str:
        """Enqueue new task"""
        try:
            task_config = self.config['tasks'].get(task_name)
            if not task_config:
                raise ValueError(f"Unknown task: {task_name}")
                
            # Generate task ID
            task_id = f"{task_name}_{datetime.utcnow().timestamp()}"
            
            # Prepare message
            message = {
                "task_id": task_id,
                "task_name": task_name,
                "payload": payload,
                "retry_count": 0,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Publish message
            await self._channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message).encode(),
                    priority=priority or task_config.get('priority', 0),
                    message_id=task_id,
                    timestamp=datetime.utcnow(),
                    headers={"x-task-name": task_name}
                ),
                routing_key=task_config['queue']
            )
            
            self.logger.info(f"Task enqueued: {task_id}")
            return task_id
            
        except Exception as e:
            self.logger.error(f"Task enqueue failed: {str(e)}")
            raise

    def register_handler(self,
                        task_name: str,
                        handler: Callable) -> None:
        """Register task handler"""
        if task_name not in self.config['tasks']:
            raise ValueError(f"Unknown task: {task_name}")
            
        self._handlers[task_name] = self._wrap_handler(handler)
        self.logger.info(f"Registered handler for {task_name}")

    async def start_processing(self) -> None:
        """Start processing tasks"""
        try:
            for task_name, task_config in self.config['tasks'].items():
                if task_name in self._handlers:
                    queue = self._queues[task_config['queue']]
                    task = asyncio.create_task(
                        self._process_queue(queue, task_name)
                    )
                    self._tasks[task_name] = task
                    
            self.logger.info("Task processing started")
            
        except Exception as e:
            self.logger.error(f"Failed to start task processing: {str(e)}")
            raise

    async def _setup_queues(self) -> None:
        """Setup task queues"""
        for task_name, task_config in self.config['tasks'].items():
            queue_name = task_config['queue']
            
            # Declare dead letter queue if configured
            if task_config.get('dead_letter_queue'):
                await self._channel.declare_queue(
                    task_config['dead_letter_queue'],
                    durable=True
                )
                
            # Declare main queue
            queue = await self._channel.declare_queue(
                queue_name,
                durable=True,
                arguments={
                    'x-max-priority': 10,
                    'x-dead-letter-exchange': '',
                    'x-dead-letter-routing-key': 
                        task_config.get('dead_letter_queue', '')
                }
            )
            
            self._queues[queue_name] = queue

    async def _process_queue(self,
                           queue: aio_pika.Queue,
                           task_name: str) -> None:
        """Process tasks from queue"""
        async with queue.iterator() as iterator:
            async for message in iterator:
                try:
                    async with message.process():
                        await self._process_message(message, task_name)
                except Exception as e:
                    self.logger.error(
                        f"Failed to process message: {str(e)}"
                    )

    async def _process_message(self,
                             message: aio_pika.IncomingMessage,
                             task_name: str) -> None:
        """Process individual message"""
        try:
            # Parse message
            content = json.loads(message.body.decode())
            task_id = content['task_id']
            
            # Update processing count
            self._processing[task_name] = \
                self._processing.get(task_name, 0) + 1
            
            try:
                # Execute handler
                handler = self._handlers[task_name]
                await handler(content['payload'])
                
                self.logger.info(f"Task completed: {task_id}")
                
            except Exception as e:
                await self._handle_task_error(message, content, str(e))
                
            finally:
                # Update processing count
                self._processing[task_name] -= 1
                
        except Exception as e:
            self.logger.error(f"Message processing failed: {str(e)}")

    async def _handle_task_error(self,
                               message: aio_pika.IncomingMessage,
                               content: Dict,
                               error: str) -> None:
        """Handle task execution error"""
        task_config = self.config['tasks'][content['task_name']]
        retry_count = content.get('retry_count', 0)
        
        if retry_count < task_config['retry_limit']:
            # Retry task
            content['retry_count'] = retry_count + 1
            content['last_error'] = error
            
            await asyncio.sleep(task_config['retry_delay'])
            await self.enqueue(
                content['task_name'],
                content['payload']
            )
            
            self.logger.warning(
                f"Task {content['task_id']} failed, retry {retry_count + 1}"
            )
        else:
            # Move to dead letter queue
            if task_config.get('dead_letter_queue'):
                await self._channel.default_exchange.publish(
                    aio_pika.Message(
                        body=json.dumps({
                            **content,
                            'final_error': error
                        }).encode()
                    ),
                    routing_key=task_config['dead_letter_queue']
                )
                
            self.logger.error(
                f"Task {content['task_id']} failed permanently: {error}"
            )

    def _wrap_handler(self, handler: Callable) -> Callable:
        """Wrap task handler with error handling and timeout"""
        @wraps(handler)
        async def wrapped(payload: Dict) -> Any:
            try:
                return await asyncio.wait_for(
                    handler(payload),
                    timeout=self.config.get('default_timeout', 300)
                )
            except asyncio.TimeoutError:
                raise TimeoutError("Task execution timed out")
                
        return wrapped 