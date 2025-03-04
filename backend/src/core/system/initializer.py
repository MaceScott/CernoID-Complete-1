from typing import Optional, Dict
import asyncio
from pathlib import Path
import logging
from core.error_handling import handle_exceptions
from core.monitoring.health_monitor import SystemHealthMonitor
from core.backup.backup_service import BackupService

class SystemInitializer:
    """System initialization and configuration"""
    
    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path(__file__).parent.parent.parent
        self.logger = self._setup_logger()
        self._initialized = False
        self._services = {}
        self._configs = {}
        self.config = ConfigManager()
        self.health_monitor = SystemHealthMonitor()
        self.backup_service = BackupService()
        self.required_services = [
            'database',
            'camera_manager',
            'face_processor',
            'notification_service',
            'permission_manager'
        ]

    async def initialize(self) -> bool:
        """Initialize the entire system"""
        try:
            self.logger.info("Starting system initialization...")
            
            # Create necessary directories
            await self._create_directories()
            
            # Load configurations
            await self._load_configurations()
            
            # Initialize core services
            await self._initialize_services()
            
            self._initialized = True
            self.logger.info("System initialization completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"System initialization failed: {str(e)}")
            await self.cleanup()
            return False

    async def _create_directories(self) -> None:
        """Create necessary system directories"""
        directories = [
            'logs',
            'data',
            'data/faces',
            'data/models',
            'data/temp',
            'config'
        ]
        
        for directory in directories:
            dir_path = self.base_path / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Created directory: {dir_path}")

    async def _load_configurations(self) -> None:
        """Load all system configurations"""
        from core.config.manager import ConfigManager
        
        config_manager = ConfigManager(self.base_path / 'config')
        self._configs = await config_manager.load_all()
        self.logger.info("Configurations loaded successfully")

    async def _initialize_services(self) -> None:
        """Initialize all core services"""
        from core.services.manager import ServiceManager
        
        service_manager = ServiceManager(self._configs)
        await service_manager.initialize_all()
        self._services = service_manager.get_services()
        self.logger.info("Core services initialized successfully")

    async def cleanup(self) -> None:
        """Cleanup system resources"""
        if self._services:
            for service in self._services.values():
                await service.cleanup()
        self.logger.info("System cleanup completed")

    def _setup_logger(self) -> logging.Logger:
        """Setup system logger"""
        logger = logging.getLogger('SystemInitializer')
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger

    @handle_exceptions(logger=system_logger.error)
    async def initialize_system(self):
        # Initialize core services
        for service in self.required_services:
            await self._init_service(service)

        # Start monitoring
        await self.health_monitor.start_monitoring()

        # Schedule regular backups
        self._schedule_backups()

        # Initialize security components
        await self._init_security()

        system_logger.info("System initialization completed successfully")

    async def _init_service(self, service_name: str):
        service = getattr(self, f"init_{service_name}")
        await service()
        system_logger.info(f"Initialized {service_name}")

    def _schedule_backups(self):
        backup_interval = self.config.get('backup.interval_hours', 24)
        asyncio.create_task(self._run_periodic_backups(backup_interval))

    async def _run_periodic_backups(self, interval_hours: int):
        while True:
            await self.backup_service.create_backup()
            await asyncio.sleep(interval_hours * 3600)
