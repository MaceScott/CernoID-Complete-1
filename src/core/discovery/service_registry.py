from typing import Dict, List, Optional
import asyncio
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import aiohttp
import consul.aio
import json
import socket

@dataclass
class ServiceInfo:
    """Service information"""
    name: str
    host: str
    port: int
    status: str
    metadata: Dict
    last_heartbeat: datetime
    health_check_url: Optional[str] = None

class ServiceRegistry:
    """Service discovery and registration"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger('ServiceRegistry')
        self._consul: Optional[consul.aio.Consul] = None
        self._services: Dict[str, ServiceInfo] = {}
        self._watchers: Dict[str, asyncio.Task] = {}
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._session_id: Optional[str] = None

    async def initialize(self) -> None:
        """Initialize service registry"""
        try:
            # Connect to Consul
            self._consul = consul.aio.Consul(
                host=self.config['consul_host'],
                port=self.config['consul_port']
            )
            
            # Create session
            self._session_id = await self._create_session()
            
            # Start heartbeat
            self._heartbeat_task = asyncio.create_task(
                self._send_heartbeat()
            )
            
            self.logger.info("Service registry initialized")
            
        except Exception as e:
            self.logger.error(f"Service registry initialization failed: {str(e)}")
            raise

    async def cleanup(self) -> None:
        """Cleanup registry resources"""
        try:
            # Cancel watchers
            for watcher in self._watchers.values():
                watcher.cancel()
                
            # Cancel heartbeat
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
                
            # Destroy session
            if self._session_id:
                await self._consul.session.destroy(self._session_id)
                
            self.logger.info("Service registry cleaned up")
            
        except Exception as e:
            self.logger.error(f"Service registry cleanup failed: {str(e)}")

    async def register_service(self,
                             name: str,
                             port: int,
                             metadata: Dict = None) -> None:
        """Register service with registry"""
        try:
            # Get host information
            host = socket.gethostname()
            
            # Prepare service info
            service = ServiceInfo(
                name=name,
                host=host,
                port=port,
                status="starting",
                metadata=metadata or {},
                last_heartbeat=datetime.utcnow(),
                health_check_url=f"http://{host}:{port}/health"
            )
            
            # Register with Consul
            await self._consul.agent.service.register(
                name=name,
                service_id=f"{name}_{host}_{port}",
                address=host,
                port=port,
                tags=["api"],
                check=consul.Check.http(
                    service.health_check_url,
                    interval="10s",
                    timeout="5s"
                )
            )
            
            self._services[name] = service
            self.logger.info(f"Registered service: {name}")
            
        except Exception as e:
            self.logger.error(f"Service registration failed: {str(e)}")
            raise

    async def deregister_service(self, name: str) -> None:
        """Deregister service from registry"""
        try:
            service = self._services.get(name)
            if service:
                service_id = f"{name}_{service.host}_{service.port}"
                await self._consul.agent.service.deregister(service_id)
                del self._services[name]
                self.logger.info(f"Deregistered service: {name}")
                
        except Exception as e:
            self.logger.error(f"Service deregistration failed: {str(e)}")
            raise

    async def get_service(self, name: str) -> Optional[ServiceInfo]:
        """Get service information"""
        try:
            # Check local cache
            if name in self._services:
                return self._services[name]
                
            # Query Consul
            services = await self._consul.catalog.service(name)
            if services:
                service = services[0]
                return ServiceInfo(
                    name=name,
                    host=service['ServiceAddress'],
                    port=service['ServicePort'],
                    status="running",
                    metadata=service.get('ServiceMeta', {}),
                    last_heartbeat=datetime.utcnow()
                )
                
            return None
            
        except Exception as e:
            self.logger.error(f"Service lookup failed: {str(e)}")
            return None

    async def watch_service(self,
                          name: str,
                          callback: Callable[[ServiceInfo], None]) -> None:
        """Watch for service changes"""
        if name in self._watchers:
            return
            
        task = asyncio.create_task(
            self._watch_service_task(name, callback)
        )
        self._watchers[name] = task

    async def _create_session(self) -> str:
        """Create Consul session"""
        session = await self._consul.session.create(
            behavior='delete',
            ttl=30
        )
        return session['ID']

    async def _send_heartbeat(self) -> None:
        """Send periodic heartbeat"""
        while True:
            try:
                # Renew session
                await self._consul.session.renew(self._session_id)
                
                # Update service status
                for service in self._services.values():
                    service.last_heartbeat = datetime.utcnow()
                    
                await asyncio.sleep(10)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Heartbeat failed: {str(e)}")
                await asyncio.sleep(5)

    async def _watch_service_task(self,
                                name: str,
                                callback: Callable[[ServiceInfo], None]) -> None:
        """Watch service task"""
        index = None
        while True:
            try:
                # Watch for changes
                services, index = await self._consul.catalog.service(
                    name,
                    index=index
                )
                
                if services:
                    service = services[0]
                    info = ServiceInfo(
                        name=name,
                        host=service['ServiceAddress'],
                        port=service['ServicePort'],
                        status="running",
                        metadata=service.get('ServiceMeta', {}),
                        last_heartbeat=datetime.utcnow()
                    )
                    callback(info)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Service watch failed: {str(e)}")
                await asyncio.sleep(5)

    async def _check_service_health(self, service: ServiceInfo) -> bool:
        """Check service health"""
        if not service.health_check_url:
            return True
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(service.health_check_url) as response:
                    return response.status == 200
                    
        except Exception:
            return False 