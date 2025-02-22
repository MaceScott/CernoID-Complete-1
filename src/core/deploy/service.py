from typing import Optional, Dict, List
import asyncio
import signal
import psutil
from pathlib import Path
import subprocess
from datetime import datetime
from ..base import BaseComponent
from ..utils.errors import handle_errors

class ServiceManager(BaseComponent):
    """Service deployment and process management"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._services: Dict[str, Dict] = {}
        self._processes: Dict[str, psutil.Process] = {}
        self._watchers: Dict[str, asyncio.Task] = {}
        
        # Service configuration
        self._service_path = Path(
            self.config.get('services.path', 'services')
        )
        self._log_path = Path(
            self.config.get('services.log_path', 'logs')
        )
        self._auto_restart = self.config.get(
            'services.auto_restart',
            True
        )

    async def initialize(self) -> None:
        """Initialize service manager"""
        # Create directories
        self._service_path.mkdir(parents=True, exist_ok=True)
        self._log_path.mkdir(parents=True, exist_ok=True)
        
        # Load service configurations
        await self._load_services()
        
        # Start configured services
        for service_id in self._services:
            if self._services[service_id].get('autostart', False):
                await self.start_service(service_id)

    async def cleanup(self) -> None:
        """Cleanup service manager resources"""
        # Stop all services
        for service_id in list(self._processes.keys()):
            await self.stop_service(service_id)
            
        self._services.clear()
        self._processes.clear()
        self._watchers.clear()

    @handle_errors(logger=None)
    async def start_service(self, service_id: str) -> None:
        """Start service"""
        if service_id not in self._services:
            raise ValueError(f"Unknown service: {service_id}")
            
        if service_id in self._processes:
            raise ValueError(f"Service already running: {service_id}")
            
        service = self._services[service_id]
        
        # Create log file
        log_file = self._log_path / f"{service_id}.log"
        log_file.touch()
        
        # Start process
        process = await self._start_process(service_id, service, log_file)
        self._processes[service_id] = process
        
        # Start watcher
        if self._auto_restart:
            self._watchers[service_id] = asyncio.create_task(
                self._watch_service(service_id)
            )

    @handle_errors(logger=None)
    async def stop_service(self, service_id: str) -> None:
        """Stop service"""
        if service_id not in self._processes:
            return
            
        # Stop watcher
        if service_id in self._watchers:
            self._watchers[service_id].cancel()
            del self._watchers[service_id]
            
        # Stop process
        process = self._processes[service_id]
        try:
            process.terminate()
            await asyncio.sleep(5)
            if process.is_running():
                process.kill()
        except psutil.NoSuchProcess:
            pass
            
        del self._processes[service_id]

    @handle_errors(logger=None)
    async def restart_service(self, service_id: str) -> None:
        """Restart service"""
        await self.stop_service(service_id)
        await self.start_service(service_id)

    def get_service_status(self, service_id: str) -> Dict:
        """Get service status"""
        if service_id not in self._services:
            raise ValueError(f"Unknown service: {service_id}")
            
        status = {
            'id': service_id,
            'config': self._services[service_id],
            'running': service_id in self._processes
        }
        
        if service_id in self._processes:
            process = self._processes[service_id]
            status.update({
                'pid': process.pid,
                'cpu_percent': process.cpu_percent(),
                'memory_percent': process.memory_percent(),
                'created': datetime.fromtimestamp(
                    process.create_time()
                ).isoformat()
            })
            
        return status

    async def _load_services(self) -> None:
        """Load service configurations"""
        for config_file in self._service_path.glob('*.yml'):
            service_id = config_file.stem
            with open(config_file) as f:
                self._services[service_id] = yaml.safe_load(f)

    async def _start_process(self,
                           service_id: str,
                           service: Dict,
                           log_file: Path) -> psutil.Process:
        """Start service process"""
        command = service['command']
        env = {**os.environ, **service.get('environment', {})}
        
        process = subprocess.Popen(
            command.split(),
            env=env,
            stdout=log_file.open('a'),
            stderr=subprocess.STDOUT,
            start_new_session=True
        )
        
        return psutil.Process(process.pid)

    async def _watch_service(self, service_id: str) -> None:
        """Watch service and restart if needed"""
        while True:
            try:
                await asyncio.sleep(5)
                
                if service_id not in self._processes:
                    break
                    
                process = self._processes[service_id]
                if not process.is_running():
                    self.logger.warning(
                        f"Service {service_id} died, restarting..."
                    )
                    await self.restart_service(service_id)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(
                    f"Service watcher failed: {str(e)}"
                )
                await asyncio.sleep(5) 