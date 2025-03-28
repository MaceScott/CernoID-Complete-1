"""Base component class."""
from typing import Any, Dict, Optional
import logging
from .utils.decorators import handle_errors

logger = logging.getLogger(__name__)

class BaseComponent:
    """Base class for all components."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize base component.
        
        Args:
            config: Optional configuration dictionary
        """
        from .logging.base import get_logger
        
        self.config = config or {}
        self.logger = get_logger(self.__class__.__name__)
        self._initialized = False
        self._initializing = False
    
    @property
    def is_initialized(self) -> bool:
        """Check if component is initialized."""
        return self._initialized
    
    @handle_errors
    async def initialize(self) -> None:
        """Initialize the component."""
        if self.is_initialized:
            self.logger.info(f"{self.__class__.__name__} already initialized")
            return
            
        if self._initializing:
            self.logger.info(f"{self.__class__.__name__} initialization already in progress")
            return
            
        try:
            self._initializing = True
            await self._do_initialize()
            self._initialized = True
            self.logger.info(f"{self.__class__.__name__} initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize {self.__class__.__name__}: {e}")
            raise
        finally:
            self._initializing = False
    
    @handle_errors
    async def cleanup(self) -> None:
        """Clean up component resources."""
        if not self.is_initialized:
            self.logger.info(f"{self.__class__.__name__} not initialized, nothing to clean up")
            return
            
        try:
            await self._do_cleanup()
            self._initialized = False
            self.logger.info(f"{self.__class__.__name__} cleaned up successfully")
        except Exception as e:
            self.logger.error(f"Failed to clean up {self.__class__.__name__}: {e}")
            raise
    
    async def _do_initialize(self) -> None:
        """
        Actual initialization implementation.
        
        Override this in subclasses to implement actual initialization logic.
        """
        pass
    
    async def _do_cleanup(self) -> None:
        """
        Actual cleanup implementation.
        
        Override this in subclasses to implement actual cleanup logic.
        """
        pass
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value with default."""
        return self.config.get(key, default)
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update configuration with new values."""
        self.config.update(new_config)
    
    @handle_errors
    async def async_initialize(self) -> None:
        """Initialize async component."""
        pass
    
    @handle_errors
    async def async_cleanup(self) -> None:
        """Clean up async component resources."""
        pass 