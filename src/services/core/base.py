from typing import Optional, Dict
from logging import Logger
from asyncio import Lock
from datetime import datetime

class BaseService:
    """Base service class for all CernoID services"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger: Logger = self._setup_logger()
        self._initialized: bool = False
        self._lock = Lock()
        self._start_time: Optional[datetime] = None

    async def initialize(self) -> bool:
        """Initialize the service with error handling"""
        if self._initialized:
            return True
            
        async with self._lock:
            try:
                self._start_time = datetime.now()
                await self._do_initialize()
                self._initialized = True
                self.logger.info(f"{self.__class__.__name__} initialized successfully")
                return True
            except Exception as e:
                self.logger.error(f"Failed to initialize {self.__class__.__name__}: {str(e)}")
                return False

    async def cleanup(self) -> None:
        """Cleanup service resources"""
        if not self._initialized:
            return
            
        async with self._lock:
            try:
                await self._do_cleanup()
                self._initialized = False
                self.logger.info(f"{self.__class__.__name__} cleaned up successfully")
            except Exception as e:
                self.logger.error(f"Cleanup failed for {self.__class__.__name__}: {str(e)}")
                raise

    async def _do_initialize(self) -> None:
        """Override this method to implement service-specific initialization"""
        raise NotImplementedError

    async def _do_cleanup(self) -> None:
        """Override this method to implement service-specific cleanup"""
        raise NotImplementedError

    def _setup_logger(self) -> Logger:
        """Setup service-specific logger"""
        from core.logging import LogManager
        return LogManager().get_logger(self.__class__.__name__) 