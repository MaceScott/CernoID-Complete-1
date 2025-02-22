from typing import Dict, Optional, Any, List, Set
import asyncio
from datetime import datetime, timedelta
import json
import uuid
from ..base import BaseComponent
from ..utils.errors import handle_errors

class ServiceRegistry(BaseComponent):
    """Service discovery and registration system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._services: Dict[str, Dict] = {}
        self._instances: Dict[str, Dict] = {}
        self._watchers: Dict[str, Set[str]] = {}
        self._ttl = self.config.get('discovery.ttl', 30)
        self._cleanup_interval = self.config.get('discovery.cleanup_interval', 10)
        self._health_interval = self.config.get('discovery.health_interval', 15)
        self._required_metadata = self.config.get(
            'discovery.required_metadata',
            ['version', 'environment']
        )

    async def initialize(self) -> None:
        """Initialize service registry"""
        # Load registered services
        await self._load_services()
        
        # Start cleanup task
        self.add_cleanup_task(
            asyncio.create_task(self._cleanup_expired())
        )
        
        # Start health check task
        if self._health_interval > 0:
            self.add_cleanup_task(
                asyncio.create_task(self._health_check())
            )

    async def cleanup(self) -> None:
        """Cleanup registry resources"""
        self._services.clear()
        self._instances.clear()
        self._watchers.clear()

    @handle_errors(logger=None)
    async def register_service(self,
                             name: str,
                             url: str,
                             metadata: Optional[Dict] = None) -> str:
        """Register service instance"""
        # Validate metadata
        metadata = metadata or {}
        missing = [
            field for field in self._required_metadata
            if field not in metadata
        ]
        if missing:
            raise ValueError(
                f"Missing required metadata: {', '.join(missing)}"
            )
            
        # Create service if not exists
        if name not in self._services:
            self._services[name] = {
                'name': name,
                'instances': set(),
                'metadata': metadata
            }
            
        # Register instance
        instance_id = str(uuid.uuid4())
        self._instances[instance_id] = {
            'id': instance_id,
            'service': name,
            'url': url.rstrip('/'),
            'metadata': metadata,
            'status': 'unknown',
            'registered': datetime.utcnow().isoformat(),
            'last_heartbeat': datetime.utcnow().isoformat()
        }
        
        self._services[name]['instances'].add(instance_id)
        
        # Notify watchers
        await self._notify_watchers(name, 'register', instance_id)
        
        return instance_id

    async def deregister_service(self,
                               instance_id: str) -> None:
        """Deregister service instance"""
        if instance_id not in self._instances:
            return
            
        instance = self._instances[instance_id]
        service_name = instance['service']
        
        # Remove instance
        del self._instances[instance_id]
        
        if service_name in self._services:
            self._services[service_name]['instances'].discard(
                instance_id
            )
            
            # Remove service if no instances
            if not self._services[service_name]['instances']:
                del self._services[service_name]
                
        # Notify watchers
        await self._notify_watchers(
            service_name,
            'deregister',
            instance_id
        )

    async def heartbeat(self, instance_id: str) -> None:
        """Update service instance heartbeat"""
        if instance_id not in self._instances:
            raise ValueError(f"Instance not found: {instance_id}")
            
        self._instances[instance_id]['last_heartbeat'] = (
            datetime.utcnow().isoformat()
        )

    async def get_services(self,
                          name: Optional[str] = None,
                          metadata: Optional[Dict] = None) -> List[Dict]:
        """Get registered services"""
        services = []
        
        if name:
            if name not in self._services:
                return []
                
            services = [self._services[name]]
        else:
            services = list(self._services.values())
            
        # Filter by metadata
        if metadata:
            services = [
                s for s in services
                if all(
                    s['metadata'].get(k) == v
                    for k, v in metadata.items()
                )
            ]
            
        # Add instance details
        for service in services:
            service['instances'] = [
                self._instances[i]
                for i in service['instances']
                if i in self._instances
            ]
            
        return services

    async def watch_service(self,
                          name: str,
                          callback: callable) -> str:
        """Watch service for changes"""
        if name not in self._services:
            raise ValueError(f"Service not found: {name}")
            
        # Register watcher
        watcher_id = str(uuid.uuid4())
        
        if name not in self._watchers:
            self._watchers[name] = set()
            
        self._watchers[name].add(watcher_id)
        
        return watcher_id

    async def unwatch_service(self,
                            name: str,
                            watcher_id: str) -> None:
        """Remove service watcher"""
        if name in self._watchers:
            self._watchers[name].discard(watcher_id)
            
            if not self._watchers[name]:
                del self._watchers[name]

    async def _notify_watchers(self,
                             service: str,
                             event: str,
                             instance_id: str) -> None:
        """Notify service watchers"""
        if service not in self._watchers:
            return
            
        # Create event data
        data = {
            'service': service,
            'event': event,
            'instance': self._instances.get(instance_id),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Notify watchers
        events = self.app.get_component('event_dispatcher')
        if events:
            await events.dispatch(
                f"service.{event}",
                data
            )

    async def _cleanup_expired(self) -> None:
        """Cleanup expired service instances"""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                
                now = datetime.utcnow()
                expired = []
                
                for instance_id, instance in self._instances.items():
                    last_heartbeat = datetime.fromisoformat(
                        instance['last_heartbeat']
                    )
                    
                    if (now - last_heartbeat).total_seconds() > self._ttl:
                        expired.append(instance_id)
                        
                # Deregister expired instances
                for instance_id in expired:
                    await self.deregister_service(instance_id)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Cleanup failed: {str(e)}")
                await asyncio.sleep(5)

    async def _health_check(self) -> None:
        """Check service instance health"""
        while True:
            try:
                await asyncio.sleep(self._health_interval)
                
                for instance in self._instances.values():
                    try:
                        # Check instance health
                        client = self.app.get_component('http_client')
                        response = await client.get(
                            f"{instance['url']}/health",
                            timeout=5
                        )
                        
                        if response.status_code == 200:
                            instance['status'] = 'healthy'
                        else:
                            instance['status'] = 'unhealthy'
                            
                    except Exception:
                        instance['status'] = 'unhealthy'
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check failed: {str(e)}")
                await asyncio.sleep(5)

    async def _load_services(self) -> None:
        """Load registered services from storage"""
        try:
            db = self.app.get_component('database')
            if not db:
                return
                
            # Load services
            services = await db.fetch_all(
                "SELECT * FROM services"
            )
            
            for service in services:
                self._services[service['name']] = {
                    'name': service['name'],
                    'instances': set(),
                    'metadata': json.loads(service['metadata'])
                }
                
            # Load instances
            instances = await db.fetch_all(
                "SELECT * FROM service_instances"
            )
            
            for instance in instances:
                await self.register_service(
                    instance['service'],
                    instance['url'],
                    json.loads(instance['metadata'])
                )
                
        except Exception as e:
            self.logger.error(f"Failed to load services: {str(e)}") 