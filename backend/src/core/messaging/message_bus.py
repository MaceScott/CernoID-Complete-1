from typing import Dict, List, Optional, Callable, Any
import asyncio
import json
from datetime import datetime
import logging
from dataclasses import dataclass
import aio_pika
from collections import defaultdict

@dataclass
class Message:
    """Message definition"""
    topic: str
    payload: Dict
    message_id: str
    timestamp: datetime
    headers: Optional[Dict] = None
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None

class MessageBus:
    """Distributed message bus system"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger('MessageBus')
        self._connection: Optional[aio_pika.Connection] = None
        self._channel: Optional[aio_pika.Channel] = None
        self._exchanges: Dict[str, aio_pika.Exchange] = {}
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._consumer_tags: List[str] = []

    async def initialize(self) -> None:
        """Initialize message bus"""
        try:
            # Connect to RabbitMQ
            self._connection = await aio_pika.connect_robust(
                self.config['rabbitmq_url']
            )
            
            # Create channel
            self._channel = await self._connection.channel()
            
            # Setup exchanges
            await self._setup_exchanges()
            
            self.logger.info("Message bus initialized")
            
        except Exception as e:
            self.logger.error(f"Message bus initialization failed: {str(e)}")
            raise

    async def cleanup(self) -> None:
        """Cleanup message bus resources"""
        try:
            # Cancel all consumers
            for tag in self._consumer_tags:
                await self._channel.basic_cancel(tag)
                
            # Close channel and connection
            if self._channel:
                await self._channel.close()
            if self._connection:
                await self._connection.close()
                
            self.logger.info("Message bus cleaned up")
            
        except Exception as e:
            self.logger.error(f"Message bus cleanup failed: {str(e)}")

    async def publish(self,
                     message: Message,
                     exchange: str = "default") -> None:
        """Publish message to bus"""
        try:
            if exchange not in self._exchanges:
                raise ValueError(f"Unknown exchange: {exchange}")
                
            # Create message
            amqp_message = aio_pika.Message(
                body=json.dumps(message.payload).encode(),
                message_id=message.message_id,
                timestamp=message.timestamp,
                headers=message.headers,
                correlation_id=message.correlation_id,
                reply_to=message.reply_to
            )
            
            # Publish message
            await self._exchanges[exchange].publish(
                amqp_message,
                routing_key=message.topic
            )
            
            self.logger.debug(
                f"Published message {message.message_id} to {message.topic}"
            )
            
        except Exception as e:
            self.logger.error(f"Message publication failed: {str(e)}")
            raise

    async def subscribe(self,
                       topic: str,
                       callback: Callable[[Message], None],
                       exchange: str = "default") -> None:
        """Subscribe to topic"""
        try:
            if exchange not in self._exchanges:
                raise ValueError(f"Unknown exchange: {exchange}")
                
            # Create queue
            queue_name = f"{topic}_{datetime.utcnow().timestamp()}"
            queue = await self._channel.declare_queue(
                queue_name,
                auto_delete=True
            )
            
            # Bind queue to exchange
            await queue.bind(
                self._exchanges[exchange],
                routing_key=topic
            )
            
            # Start consuming
            consumer_tag = await queue.consume(
                self._message_handler(callback)
            )
            self._consumer_tags.append(consumer_tag)
            
            # Store subscriber
            self._subscribers[topic].append(callback)
            
            self.logger.info(f"Subscribed to topic: {topic}")
            
        except Exception as e:
            self.logger.error(f"Subscription failed: {str(e)}")
            raise

    async def request(self,
                     message: Message,
                     timeout: int = 30,
                     exchange: str = "default") -> Optional[Message]:
        """Send request and wait for response"""
        try:
            if not message.reply_to:
                # Create response queue
                response_queue = await self._channel.declare_queue(
                    "",
                    auto_delete=True
                )
                message.reply_to = response_queue.name
                
            # Create future for response
            future = asyncio.Future()
            
            # Subscribe to response
            await response_queue.consume(
                self._response_handler(future)
            )
            
            # Send request
            await self.publish(message, exchange)
            
            # Wait for response
            try:
                response = await asyncio.wait_for(future, timeout)
                return response
            except asyncio.TimeoutError:
                self.logger.warning(
                    f"Request {message.message_id} timed out"
                )
                return None
                
        except Exception as e:
            self.logger.error(f"Request failed: {str(e)}")
            raise

    async def _setup_exchanges(self) -> None:
        """Setup message exchanges"""
        for exchange_name, exchange_type in self.config['exchanges'].items():
            exchange = await self._channel.declare_exchange(
                exchange_name,
                type=exchange_type,
                durable=True
            )
            self._exchanges[exchange_name] = exchange

    def _message_handler(self,
                        callback: Callable[[Message], None]) -> Callable:
        """Create message handler"""
        async def handler(message: aio_pika.IncomingMessage) -> None:
            async with message.process():
                try:
                    # Parse message
                    payload = json.loads(message.body.decode())
                    
                    # Create message object
                    msg = Message(
                        topic=message.routing_key,
                        payload=payload,
                        message_id=message.message_id,
                        timestamp=message.timestamp,
                        headers=message.headers,
                        correlation_id=message.correlation_id,
                        reply_to=message.reply_to
                    )
                    
                    # Call callback
                    await callback(msg)
                    
                except Exception as e:
                    self.logger.error(
                        f"Message handling failed: {str(e)}"
                    )
                    
        return handler

    def _response_handler(self,
                         future: asyncio.Future) -> Callable:
        """Create response handler"""
        async def handler(message: aio_pika.IncomingMessage) -> None:
            async with message.process():
                try:
                    # Parse response
                    payload = json.loads(message.body.decode())
                    
                    # Create message object
                    response = Message(
                        topic=message.routing_key,
                        payload=payload,
                        message_id=message.message_id,
                        timestamp=message.timestamp,
                        headers=message.headers,
                        correlation_id=message.correlation_id
                    )
                    
                    # Set future result
                    if not future.done():
                        future.set_result(response)
                        
                except Exception as e:
                    self.logger.error(
                        f"Response handling failed: {str(e)}"
                    )
                    if not future.done():
                        future.set_exception(e)
                        
        return handler 