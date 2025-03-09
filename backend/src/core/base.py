"""Base component class."""
from typing import Any
from .utils.errors import handle_errors
from .logging import get_logger

logger = get_logger(__name__)

class BaseComponent:
    """Base class for all components."""
    
    @handle_errors
    def initialize(self) -> None:
        """Initialize the component."""
        pass
    
    @handle_errors
    def cleanup(self) -> None:
        """Clean up component resources."""
        pass
    
    @handle_errors
    async def async_initialize(self) -> None:
        """Initialize async component."""
        pass
    
    @handle_errors
    async def async_cleanup(self) -> None:
        """Clean up async component resources."""
        pass
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default) 