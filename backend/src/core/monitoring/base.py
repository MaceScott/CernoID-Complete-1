"""Base component for the monitoring system."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import structlog

logger = structlog.get_logger()

class BaseComponent(ABC):
    """Base class for all monitoring components."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize the base component.
        
        Args:
            name: The name of the component.
            config: Optional configuration dictionary.
        """
        self.name = name
        self.config = config or {}
        self.logger = logger.bind(component=name)
        self._initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the component."""
        self._initialized = True
        self.logger.info("Component initialized", name=self.name)

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up the component."""
        self._initialized = False
        self.logger.info("Component cleaned up", name=self.name)

    @property
    def is_initialized(self) -> bool:
        """Check if the component is initialized."""
        return self._initialized

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            key: The configuration key.
            default: The default value if the key doesn't exist.
        
        Returns:
            The configuration value.
        """
        return self.config.get(key, default)

    def set_config(self, key: str, value: Any) -> None:
        """Set a configuration value.
        
        Args:
            key: The configuration key.
            value: The value to set.
        """
        self.config[key] = value
        self.logger.debug("Config updated", key=key) 