from typing import Dict, Optional, Any, List, Union, Callable
import asyncio
from datetime import datetime, timedelta
import traceback

class Consumer:
    """Queue consumer"""
    
    def __init__(self,
                 consumer_id: str,
                 queue: 'Queue',
                 handlers: Dict[str, Callable],
                 max_retries: int,
                 retry_delay: int,
                 manager: Any):
        self.id = consumer_id
        self._queue = queue
        self._handlers = handlers
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._manager = manager
        self._running = True
        self._current_message = None

    async def run(self) -> None:
        """Run consumer"""
        while self._running:
            try:
                # Get message from queue
                message = await self._queue.get()
                self._current_message = message
                
                # Process message
                await self._process_message(message)
                
                # Mark message as done
                self._queue.task_done()
                self._current_message = None
                
            except asyncio.CancelledError:
                break
                
            except Exception as e:
                self._manager.logger.error(
                    f"Consumer error: {str(e)}"
                )
                await asyncio.sleep(1)

    async def stop(self) -> None:
        """Stop consumer"""
        self._running = False
        
        # Return current message to queue
        if self._current_message:
            await self._queue.put(self._current_message)

    async def _process_message(self, message: Dict) -> None:
        """Process queue message"""
        try:
            # Get message data
            event = message['metadata'].get('event')
            if not event:
                raise ValueError("Missing event type")
                
            # Get handler
            handler = self._handlers.get(event)
            if not handler:
                raise ValueError(f"No handler for event: {event}")
                
            # Execute handler
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message['data'])
                else:
                    handler(message['data'])
                    
                self._manager._stats['consumed'] += 1
                
                # Emit event
                await self._manager.app.events.emit(
                    'queue.consumed',
                    {
                        'queue': self._queue.name,
                        'message_id': message['id'],
                        'consumer_id': self.id
                    }
                )
                
            except Exception as e:
                # Handle retry
                if message['retries'] < self._max_retries:
                    await self._retry_message(message, str(e))
                else:
                    await self._handle_failure(message, str(e))
                    
        except Exception as e:
            self._manager.logger.error(
                f"Message processing error: {str(e)}"
            )
            await self._handle_failure(message, str(e))

    async def _retry_message(self,
                           message: Dict,
                           error: str) -> None:
        """Retry failed message"""
        try:
            # Update retry count
            message['retries'] += 1
            
            # Add error info
            message['last_error'] = {
                'message': error,
                'timestamp': datetime.utcnow().isoformat(),
                'traceback': traceback.format_exc()
            }
            
            # Calculate delay
            delay = self._retry_delay * message['retries']
            
            # Schedule retry
            await asyncio.sleep(delay)
            await self._queue.put(message)
            
            self._manager._stats['retried'] += 1
            
            # Emit event
            await self._manager.app.events.emit(
                'queue.retried',
                {
                    'queue': self._queue.name,
                    'message_id': message['id'],
                    'retries': message['retries'],
                    'error': error
                }
            )
            
        except Exception as e:
            self._manager.logger.error(
                f"Message retry error: {str(e)}"
            )
            await self._handle_failure(message, str(e))

    async def _handle_failure(self,
                            message: Dict,
                            error: str) -> None:
        """Handle message failure"""
        try:
            self._manager._stats['failed'] += 1
            
            # Emit event
            await self._manager.app.events.emit(
                'queue.failed',
                {
                    'queue': self._queue.name,
                    'message_id': message['id'],
                    'error': error,
                    'retries': message['retries']
                }
            )
            
            # Store failed message
            await self._queue.store_failed(message, error)
            
        except Exception as e:
            self._manager.logger.error(
                f"Failure handling error: {str(e)}"
            ) 