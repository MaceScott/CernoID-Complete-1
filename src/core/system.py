alembic revision --autogenerate -m "Initial migration"
alembic upgrade head 

import asyncio
from typing import Optional, Dict
from .services.manager import ServiceManager
from .config.manager import ConfigManager
from .monitoring.metrics import MetricsCollector
from .events.event_bus import EventBus

async def main():
    system = CernoIDSystem()
    await system.start()

class CernoIDSystem:
    """Main system initialization and management"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_manager = ConfigManager(config_path)
        self.service_manager = ServiceManager()
        self.event_bus = EventBus()
        self.metrics = MetricsCollector()
        self.logger = self._setup_logger()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the entire system"""
        if self._initialized:
            return

        try:
            # Initialize core components
            self.logger.info("Initializing CernoID system...")
            await self.event_bus.start()
            await self.metrics.start()
            
            # Register and initialize services
            await self._register_services()
            await self.service_manager.initialize_all()
            
            self._initialized = True
            self.logger.info("CernoID system initialized successfully")
        except Exception as e:
            self.logger.error(f"System initialization failed: {str(e)}")
            await self.cleanup()
            raise

    async def cleanup(self) -> None:
        """Cleanup system resources"""
        try:
            await self.service_manager.cleanup_all()
            await self.event_bus.stop()
            await self.metrics.stop()
            self._initialized = False
            self.logger.info("System cleanup completed")
        except Exception as e:
            self.logger.error(f"Cleanup failed: {str(e)}")
            raise

    async def _register_services(self) -> None:
        """Register all required services"""
        from .services.recognition import RecognitionService
        from .services.camera import CameraService
        from .services.database import DatabaseService
        
        # Initialize services with dependencies
        db_service = DatabaseService(self.config_manager.get('database'))
        camera_service = CameraService(self.config_manager.get('camera'))
        recognition_service = RecognitionService(
            database_service=db_service,
            config=self.config_manager.get('recognition')
        )
        
        # Register services
        await self.service_manager.register_service(DatabaseService, db_service)
        await self.service_manager.register_service(CameraService, camera_service)
        await self.service_manager.register_service(RecognitionService, recognition_service)

if __name__ == "__main__":
    asyncio.run(main()) 
