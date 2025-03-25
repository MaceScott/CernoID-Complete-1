from typing import Optional, Dict
import asyncio
from pathlib import Path
import logging
from core.config.manager import ConfigManager
from core.services.manager import ServiceManager
from core.database.session import DatabaseSession
from core.events.event_bus import EventBus
from core.monitoring.metrics import MetricsCollector
from core.config import settings

class SystemBootstrap:
    """System bootstrap and initialization manager"""
    
    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path("/app/config/config.yaml")
        self.config_manager = ConfigManager(config_path)
        self.logger = self._setup_logger()
        self._initialized = False
        self._components = {}
        self._health_check_task = None

    async def initialize(self) -> bool:
        """Initialize all system components"""
        try:
            self.logger.info("Starting system initialization...")
            
            # Load configuration
            config = await self.config_manager.load_all()
            
            # Initialize core components in order
            await self._init_database(config)
            await self._init_event_system(config)
            await self._init_services(config)
            await self._init_monitoring(config)
            
            # Start health check
            self._health_check_task = asyncio.create_task(
                self._periodic_health_check()
            )
            
            self._initialized = True
            self.logger.info("System initialization completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"System initialization failed: {str(e)}")
            await self.cleanup()
            raise

    async def _init_database(self, config: Dict) -> None:
        """Initialize database connection and run migrations"""
        try:
            db_session = DatabaseSession(settings.DATABASE_URL)
            await db_session.create_all()
            
            # Run migrations
            from core.database.migrations.manager import MigrationManager
            migration_manager = MigrationManager(Path("/app/migrations"))
            await migration_manager.run_migrations()
            
            self._components['database'] = db_session
            self.logger.info("Database initialization completed")
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {str(e)}")
            raise

    async def _init_event_system(self, config: Dict) -> None:
        """Initialize event system"""
        try:
            event_bus = EventBus()
            await event_bus.start()
            self._components['event_bus'] = event_bus
            self.logger.info("Event system initialization completed")
            
        except Exception as e:
            self.logger.error(f"Event system initialization failed: {str(e)}")
            raise

    async def _init_services(self, config: Dict) -> None:
        """Initialize service manager and services"""
        try:
            service_manager = ServiceManager(self.config_manager)
            await service_manager.initialize()
            self._components['services'] = service_manager
            self.logger.info("Services initialization completed")
            
        except Exception as e:
            self.logger.error(f"Services initialization failed: {str(e)}")
            raise

    async def _init_monitoring(self, config: Dict) -> None:
        """Initialize monitoring system"""
        try:
            metrics_collector = MetricsCollector(config)
            await metrics_collector.initialize()
            self._components['monitoring'] = metrics_collector
            self.logger.info("Monitoring system initialization completed")
            
        except Exception as e:
            self.logger.error(f"Monitoring initialization failed: {str(e)}")
            raise

    async def _periodic_health_check(self) -> None:
        """Perform periodic health checks"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                health_status = await self.check_health()
                
                if not health_status['healthy']:
                    self.logger.warning(
                        f"Health check failed: {health_status['details']}"
                    )
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check failed: {str(e)}")

    async def check_health(self) -> Dict:
        """Check system health"""
        health_status = {
            "healthy": True,
            "details": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Check database
        try:
            await self._components['database'].ping()
            health_status['details']['database'] = "healthy"
        except Exception as e:
            health_status['healthy'] = False
            health_status['details']['database'] = str(e)

        # Check services
        service_status = await self._components['services'].check_health()
        health_status['details']['services'] = service_status
        if not all(status == "healthy" for status in service_status.values()):
            health_status['healthy'] = False

        return health_status

    async def cleanup(self) -> None:
        """Cleanup system resources"""
        self.logger.info("Starting system cleanup...")
        
        if self._health_check_task:
            self._health_check_task.cancel()
            
        cleanup_order = ['monitoring', 'services', 'event_bus', 'database']
        
        for component in cleanup_order:
            if component in self._components:
                try:
                    await self._components[component].cleanup()
                    self.logger.info(f"Cleaned up {component}")
                except Exception as e:
                    self.logger.error(f"Failed to cleanup {component}: {str(e)}")

        self._initialized = False
        self.logger.info("System cleanup completed")

    def _setup_logger(self) -> logging.Logger:
        """Setup system logger"""
        logger = logging.getLogger('SystemBootstrap')
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger 