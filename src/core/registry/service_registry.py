from typing import Dict, List, Optional, Any, Tuple
import asyncio
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import json
import aiohttp
import consul.aio
import etcd3.aio as etcd
import socket
import hashlib
import random

@dataclass
class ServiceInstance:
    """Service instance information"""
    id: str
    name: str
    host: str
    port: int
    metadata: Dict
    health_check_url: Optional[str]
    status: str = "unknown"
    last_heartbeat: Optional[datetime] = None
    registration_time: Optional[datetime] = None

class ServiceRegistry:
    """Enhanced service registry implementation"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger('ServiceRegistry')
        self._consul: Optional[consul.aio.Consul] = None
        self._etcd: Optional[etcd.client] = None
        self._services: Dict[str, Dict[str, ServiceInstance]] = {}
        self._watchers: Dict[str, asyncio.Task] = {}
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._session_id: Optional[str] = None
        self._local_cache: Dict[str, List[ServiceInstance]] = {}
        self._cache_ttl = timedelta(seconds=config.get('cache_ttl', 60))

    async def initialize(self) -> None:
        """Initialize service registry"""
        try:
            # Initialize Consul client
            if self.config.get('use_consul', True):
                self._consul = consul.aio.Consul(
                    host=self.config['consul_host'],
                    port=self.config['consul_port']
                )
                self._session_id = await self._create_session()
                
            # Initialize etcd client
            if self.config.get('use_etcd', False):
                self._etcd = await etcd.client(
                    host=self.config['etcd_host'],
                    port=self.config['etcd_port']
                )
                
            # Start background tasks
            self._heartbeat_task = asyncio.create_task(
                self._send_heartbeat()
            )
            self._cleanup_task = asyncio.create_task(
                self._cleanup_services()
            )
            
            self.logger.info("Service registry initialized")
            
        except Exception as e:
            self.logger.error(f"Service registry initialization failed: {str(e)}")
            raise

    async def register_service(self,
                             service: ServiceInstance) -> bool:
        """Register service instance"""
        try:
            # Generate service ID if not provided
            if not service.id:
                service.id = self._generate_service_id(service)
                
            service.registration_time = datetime.utcnow()
            service.last_heartbeat = datetime.utcnow()
            
            # Store in local registry
            if service.name not in self._services:
                self._services[service.name] = {}
            self._services[service.name][service.id] = service
            
            # Register with Consul
            if self._consul:
                success = await self._register_consul(service)
                if not success:
                    return False
                    
            # Register with etcd
            if self._etcd:
                success = await self._register_etcd(service)
                if not success:
                    return False
                    
            self.logger.info(
                f"Registered service: {service.name} ({service.id})"
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Service registration failed: {str(e)}")
            return False

    async def deregister_service(self,
                               service_name: str,
                               service_id: str) -> bool:
        """Deregister service instance"""
        try:
            # Remove from local registry
            if service_name in self._services:
                self._services[service_name].pop(service_id, None)
                
            # Deregister from Consul
            if self._consul:
                await self._consul.agent.service.deregister(service_id)
                
            # Deregister from etcd
            if self._etcd:
                key = f"/services/{service_name}/{service_id}"
                await self._etcd.delete(key)
                
            self.logger.info(
                f"Deregistered service: {service_name} ({service_id})"
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Service deregistration failed: {str(e)}")
            return False

    async def get_service(self,
                         service_name: str,
                         use_cache: bool = True) -> List[ServiceInstance]:
        """Get service instances"""
        try:
            # Check cache if enabled
            if use_cache and service_name in self._local_cache:
                cache_time = self._local_cache[service_name][0]
                if datetime.utcnow() - cache_time < self._cache_ttl:
                    return self._local_cache[service_name][1]
                    
            instances = []
            
            # Get from Consul
            if self._consul:
                services = await self._consul.catalog.service(service_name)
                for service in services[0]:
                    instance = ServiceInstance(
                        id=service['ServiceID'],
                        name=service_name,
                        host=service['ServiceAddress'],
                        port=service['ServicePort'],
                        metadata=service.get('ServiceMeta', {}),
                        health_check_url=service.get('ServiceCheck', {}).get('HTTP'),
                        status="healthy"
                    )
                    instances.append(instance)
                    
            # Get from etcd
            if self._etcd:
                prefix = f"/services/{service_name}/"
                result = await self._etcd.get_prefix(prefix)
                for value, _ in result:
                    service_data = json.loads(value)
                    instance = ServiceInstance(**service_data)
                    instances.append(instance)
                    
            # Update cache
            self._local_cache[service_name] = (
                datetime.utcnow(),
                instances
            )
            
            return instances
            
        except Exception as e:
            self.logger.error(f"Service lookup failed: {str(e)}")
            return []

    async def watch_service(self,
                          service_name: str,
                          callback: callable) -> None:
        """Watch for service changes"""
        if service_name in self._watchers:
            return
            
        async def watch_task():
            index = None
            while True:
                try:
                    if self._consul:
                        services, index = await self._consul.catalog.service(
                            service_name,
                            index=index
                        )
                        instances = [
                            ServiceInstance(
                                id=svc['ServiceID'],
                                name=service_name,
                                host=svc['ServiceAddress'],
                                port=svc['ServicePort'],
                                metadata=svc.get('ServiceMeta', {}),
                                health_check_url=svc.get('ServiceCheck', {}).get('HTTP'),
                                status="healthy"
                            )
                            for svc in services
                        ]
                        await callback(instances)
                        
                    elif self._etcd:
                        async for event in self._etcd.watch_prefix(
                            f"/services/{service_name}/"
                        ):
                            instances = await self.get_service(
                                service_name,
                                use_cache=False
                            )
                            await callback(instances)
                            
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"Service watch failed: {str(e)}")
                    await asyncio.sleep(5)
                    
        self._watchers[service_name] = asyncio.create_task(watch_task())

    async def cleanup(self) -> None:
        """Cleanup registry resources"""
        try:
            # Cancel background tasks
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
            if self._cleanup_task:
                self._cleanup_task.cancel()
                
            for task in self._watchers.values():
                task.cancel()
                
            # Wait for tasks to complete
            await asyncio.gather(
                *[task for task in self._watchers.values()],
                return_exceptions=True
            )
            
            # Close connections
            if self._consul:
                await self._consul.close()
            if self._etcd:
                await self._etcd.close()
                
            self.logger.info("Service registry cleaned up")
            
        except Exception as e:
            self.logger.error(f"Registry cleanup failed: {str(e)}")

    def _generate_service_id(self, service: ServiceInstance) -> str:
        """Generate unique service ID"""
        components = [
            service.name,
            service.host,
            str(service.port),
            socket.gethostname(),
            str(random.randint(0, 1000000))
        ]
        return hashlib.md5(
            "-".join(components).encode()
        ).hexdigest()

    async def _register_consul(self, service: ServiceInstance) -> bool:
        """Register service with Consul"""
        try:
            service_def = {
                'name': service.name,
                'service_id': service.id,
                'address': service.host,
                'port': service.port,
                'meta': service.metadata
            }
            
            if service.health_check_url:
                service_def['check'] = {
                    'http': service.health_check_url,
                    'interval': '10s',
                    'timeout': '5s'
                }
                
            return await self._consul.agent.service.register(**service_def)
            
        except Exception as e:
            self.logger.error(f"Consul registration failed: {str(e)}")
            return False

    async def _register_etcd(self, service: ServiceInstance) -> bool:
        """Register service with etcd"""
        try:
            key = f"/services/{service.name}/{service.id}"
            value = json.dumps(service.__dict__)
            await self._etcd.put(key, value)
            return True
            
        except Exception as e:
            self.logger.error(f"etcd registration failed: {str(e)}")
            return False 