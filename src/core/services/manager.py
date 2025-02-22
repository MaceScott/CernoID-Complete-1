from typing import Dict, Type, Any
import asyncio
from .base import BaseService
from core.utils.decorators import async_retry

class ServiceManager:
    """Manage system services lifecycle"""
    
    def __init__(self, configs: Dict[str, Any]):
        self.configs = configs
        self.services: Dict[str, Any] = {}
        self.logger = self._setup_logger()
        self._initialized = False
        self._lock = asyncio.Lock()

    @async_retry(retries=3, delay=1.0)
    async def initialize_all(self) -> None:
        """Initialize all system services"""
        if self._initialized:
            return

        async with self._lock:
            try:
                # Initialize database service first
                await self._init_database()
                
                # Initialize other core services
                await self._init_event_system()
                await self._init_cache_system()
                await self._init_recognition_system()
                
                self._initialized = True
                self.logger.info("All services initialized successfully")
                
            except Exception as e:
                self.logger.error(f"Service initialization failed: {str(e)}")
                await self.cleanup()
                raise

    async def _init_database(self) -> None:
        """Initialize database service"""
        from core.database.service import DatabaseService
        
        db_service = DatabaseService(self.configs.get('database', {}))
        await db_service.initialize()
        self.services['database'] = db_service
        self.logger.info("Database service initialized")

    async def _init_event_system(self) -> None:
        """Initialize event system"""
        from core.events.event_bus import EventBus
        
        event_bus = EventBus()
        await event_bus.start()
        self.services['event_bus'] = event_bus
        self.logger.info("Event system initialized")

    async def _init_cache_system(self) -> None:
        """Initialize caching system"""
        from core.cache.manager import CacheManager
        
        cache_manager = CacheManager(self.configs.get('cache', {}))
        await cache_manager.initialize()
        self.services['cache'] = cache_manager
        self.logger.info("Cache system initialized")

    async def _init_recognition_system(self) -> None:
        """Initialize recognition system"""
        from core.recognition.service import RecognitionService
        
        recognition_service = RecognitionService(
            self.configs.get('recognition', {}),
            self.services['database'],
            self.services['cache']
        )
        await recognition_service.initialize()
        self.services['recognition'] = recognition_service
        self.logger.info("Recognition system initialized")

    async def cleanup(self) -> None:
        """Cleanup all services"""
        for service_name, service in self.services.items():
            try:
                await service.cleanup()
                self.logger.info(f"Cleaned up {service_name} service")
            except Exception as e:
                self.logger.error(f"Failed to cleanup {service_name}: {str(e)}")

    def get_service(self, service_name: str) -> Any:
        """Get a service instance by name"""
        if not self._initialized:
            raise RuntimeError("Services not initialized")
            
        service = self.services.get(service_name)
        if not service:
            raise KeyError(f"Service not found: {service_name}")
            
        return service

    def get_services(self) -> Dict[str, Any]:
        """Get all service instances"""
        return self.services

    def _setup_logger(self):
        """Setup service manager logger"""
        from core.logging import LogManager
        return LogManager().get_logger("ServiceManager")

    async def register_service(self, service_type: Type[BaseService], service: BaseService):
        """Register a service instance"""
        self.services[service_type.__name__] = service
        self.logger.info(f"Registered service: {service_type.__name__}")
        
    async def get_service(self, service_type: Type[BaseService]) -> BaseService:
        """Get a service instance"""
        if service_type.__name__ not in self.services:
            raise ServiceError(f"Service not registered: {service_type.__name__}")
        return self.services[service_type.__name__]
        
    async def initialize_all(self):
        """Initialize all registered services"""
        for service_type, service in self.services.items():
            try:
                await service.initialize()
            except Exception as e:
                raise ServiceError(f"Failed to initialize {service_type}: {str(e)}")
                
    async def cleanup_all(self):
        """Cleanup all registered services"""
        for service_type, service in self.services.items():
            try:
                await service.cleanup()
            except Exception as e:
                self.logger.error(f"Cleanup failed for {service_type}: {str(e)}") 