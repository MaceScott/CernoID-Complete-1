"""Service manager module."""
from typing import Dict, Any, Optional
import logging
from pathlib import Path

from core.config.manager import ConfigManager
from core.logging.base import get_logger

class ServiceManager:
    """Manages application services and their lifecycle."""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.logger = get_logger(__name__)
        if config_manager is None:
            config_path = Path("/app/config/config.yaml")
            self.config_manager = ConfigManager(config_path)
        else:
            self.config_manager = config_manager
        self._services = {}
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize all registered services."""
        try:
            self.logger.info("Initializing services...")
            
            # Load service configurations
            config = await self.config_manager.load_all()
            
            # Initialize each service
            for service_name, service in self._services.items():
                self.logger.info(f"Initializing service: {service_name}")
                await service.initialize(config.get(service_name, {}))
            
            self._initialized = True
            self.logger.info("Services initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Service initialization failed: {str(e)}")
            await self.cleanup()
            raise

    async def cleanup(self) -> None:
        """Cleanup all services."""
        try:
            self.logger.info("Cleaning up services...")
            
            # Cleanup each service in reverse order
            for service_name, service in reversed(list(self._services.items())):
                try:
                    self.logger.info(f"Cleaning up service: {service_name}")
                    await service.cleanup()
                except Exception as e:
                    self.logger.error(f"Error cleaning up service {service_name}: {str(e)}")
            
            self._initialized = False
            self.logger.info("Services cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Service cleanup failed: {str(e)}")
            raise

    def register_service(self, name: str, service: Any) -> None:
        """Register a new service."""
        self._services[name] = service
        self.logger.info(f"Registered service: {name}")

    def get_service(self, name: str) -> Optional[Any]:
        """Get a registered service by name."""
        return self._services.get(name)

    @property
    def is_initialized(self) -> bool:
        """Check if services are initialized."""
        return self._initialized

# Create singleton instance
service_manager = ServiceManager() 