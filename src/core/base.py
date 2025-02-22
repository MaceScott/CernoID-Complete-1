from typing import Dict, Optional, TypeVar, Any
import logging
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from .utils.errors import handle_errors
from .utils.metrics import track_time
from .config import ConfigManager

T = TypeVar('T')

class BaseComponent(ABC):
    """Base class for all core components"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = ConfigManager(config)
        self.name = self.__class__.__name__
        self.logger = logging.getLogger(self.name)
        self._initialized = False
        self._start_time: Optional[datetime] = None
        self._cleanup_tasks: list[asyncio.Task] = []

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize component"""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup component resources"""
        pass

    @handle_errors(raise_error=True)
    async def start(self) -> None:
        """Start the component"""
        if self._initialized:
            raise RuntimeError(f"{self.name} is already initialized")
            
        self._start_time = datetime.utcnow()
        await self.initialize()
        self._initialized = True
        self.logger.info(f"{self.name} initialized successfully")

    @handle_errors(raise_error=False)
    async def stop(self) -> None:
        """Stop the component"""
        if not self._initialized:
            return
            
        # Cancel all cleanup tasks
        for task in self._cleanup_tasks:
            task.cancel()
            
        await self.cleanup()
        self._initialized = False
        self.logger.info(f"{self.name} stopped successfully")

    async def __aenter__(self) -> 'BaseComponent':
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.stop()

    def add_cleanup_task(self, task: asyncio.Task) -> None:
        """Add task to cleanup list"""
        self._cleanup_tasks.append(task)

    @property
    def uptime(self) -> Optional[float]:
        """Get component uptime in seconds"""
        if not self._start_time:
            return None
        return (datetime.utcnow() - self._start_time).total_seconds()

    @property
    def is_initialized(self) -> bool:
        """Check if component is initialized"""
        return self._initialized 