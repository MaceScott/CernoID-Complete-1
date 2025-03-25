"""Error definitions for the monitoring system."""
import functools
import logging
from typing import Optional, Callable, Any

class MonitorError(Exception):
    """Base class for monitoring errors."""

    def __init__(self, message: str, *args, **kwargs):
        """Initialize the error.
        
        Args:
            message: The error message.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(message, *args)
        self.message = message
        for key, value in kwargs.items():
            setattr(self, key, value)

class ComponentInitializationError(MonitorError):
    """Raised when a component fails to initialize."""
    pass

class ComponentCleanupError(MonitorError):
    """Raised when a component fails to clean up."""
    pass

class MetricCollectionError(MonitorError):
    """Raised when metric collection fails."""
    pass

class SystemResourceError(MonitorError):
    """Raised when there's an error accessing system resources."""
    pass

class ConfigurationError(MonitorError):
    """Raised when there's an error in the configuration."""
    pass

class ThresholdExceededError(MonitorError):
    """Raised when a monitored value exceeds its threshold."""
    pass

class MetricsError(MonitorError):
    """Raised when there's an error in metrics handling."""
    pass

def handle_errors(logger: Optional[logging.Logger] = None) -> Callable:
    """Decorator to handle errors in monitoring functions.
    
    Args:
        logger: Optional logger instance. If None, errors will be propagated.
        
    Returns:
        Decorator function that handles errors.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if logger:
                    logger.error(f"Error in {func.__name__}: {str(e)}")
                raise MetricsError(f"Operation failed: {str(e)}")
        return wrapper
    return decorator 