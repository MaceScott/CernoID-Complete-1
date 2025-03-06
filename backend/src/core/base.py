"""Base component class for application components."""
from typing import Any, Dict
from src.core.utils.errors import handle_errors
from src.core.logging import get_logger

logger = get_logger(__name__)

class BaseComponent:
    """Base class for application components."""
    
    def __init__(self):
        """Initialize component."""
        pass
    
    @handle_errors(logger=logger)
    async def initialize(self) -> None:
        """Initialize component."""
        pass
    
    @handle_errors(logger=logger)
    async def cleanup(self) -> None:
        """Cleanup component resources."""
        pass
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default) 