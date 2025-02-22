from typing import Dict, Optional, Any, List, Deque
import asyncio
from collections import deque
from datetime import datetime, timedelta
from ...base import BaseComponent

class MemoryBackend(BaseComponent):
    """In-memory queue backend"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._queues: Dict[str, Deque] = {}
        self._delayed: Dict[str, List[Dict]] = {}
        self._max_size = self.config.get('queue.max_size', 10000)
        self._cleanup_interval = self.config.get(
            'queue.cleanup_interval',
            60
        )

    async def initialize(self) -> None:
        """Initialize memory backend"""
        # Start delayed message processor
        asyncio.create_task(self._process_delayed())
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_task())

    async def cleanup(self) -> None:
        """Cleanup backend resources"""
        self._queues.clear()
        self._delayed.clear()

    async def publish(self,
                     queue: str,
                     message: Any,
                     delay: Optional[int] = None) -> bool:
        """Publish message to queue"""
        # Handle delayed message
        if delay:
            when = datetime.utcnow() + timedelta(seconds=delay)
            
            if queue not in self._delayed:
                self._delayed[queue] = []
                
            self._delayed[queue].append({
                'message': message,
                'when': when
            })
            return True
            
        # Check queue exists
        if queue not in self._queues:
            self._queues[queue] = deque()
            
        # Check size limit
        if len(self._queues[queue]) >= self._max_size:
            return False
            
        # Add message
        self._queues[queue].append(message)
        return True

    async def get(self, queue: str) -> Optional[Any]:
        """Get message from queue"""
        if queue not in self._queues:
            return None
            
        try:
            return self._queues[queue].popleft()
        except IndexError:
            return None

    async def ack(self,
                  queue: str,
                  message: Any) -> bool:
        """Acknowledge message"""
        # No need to ack in memory backend
        return True

    async def get_stats(self) -> Dict[str, Any]:
        """Get backend statistics"""
        stats = {
            'queues': len(self._queues),
            'delayed': len(self._delayed)
        }
        
        # Add queue sizes
        for queue, messages in self._queues.items():
            stats[f"queue_{queue}_size"] = len(messages)
            
        return stats

    async def _process_delayed(self) -> None:
        """Process delayed messages"""
        while True:
            try:
                now = datetime.utcnow()
                
                # Check all queues
                for queue in list(self._delayed.keys()):
                    # Get due messages
                    due = [
                        m for m in self._delayed[queue]
                        if now >= m['when']
                    ]
                    
                    # Publish due messages
                    for message in due:
                        await self.publish(
                            queue,
                            message['message']
                        )
                        
                    # Remove published messages
                    self._delayed[queue] = [
                        m for m in self._delayed[queue]
                        if now < m['when']
                    ]
                    
                    # Remove empty queues
                    if not self._delayed[queue]:
                        del self._delayed[queue]
                        
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(
                    f"Delayed message processor error: {str(e)}"
                )
                await asyncio.sleep(1)

    async def _cleanup_task(self) -> None:
        """Cleanup task"""
        while True:
            try:
                # Remove empty queues
                for queue in list(self._queues.keys()):
                    if not self._queues[queue]:
                        del self._queues[queue]
                        
                await asyncio.sleep(self._cleanup_interval)
                
            except Exception as e:
                self.logger.error(f"Cleanup error: {str(e)}")
                await asyncio.sleep(self._cleanup_interval) 