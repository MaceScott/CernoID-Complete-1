from typing import Dict, Optional, Any, List, Callable
import asyncio
from datetime import datetime
import json
import random
from ..base import BaseComponent
from ..utils.errors import handle_errors

class ServiceClient(BaseComponent):
    """Service discovery client"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._registry = None
        self._instance_id: Optional[str] = None
        self._heartbeat_interval = self.config.get(
            'discovery.heartbeat_interval',
            10
        )
        self._cache_ttl = self.config.get('discovery.cache_ttl', 60)
        self._cache: Dict[str, Dict] = {}
        self._watchers: Dict[str, List[Callable]] = {}
        self._load_balancer = self.config.get(
            'discovery.load_balancer',
            'round_robin'
        )

    async def initialize(self) -> None:
        """Initialize service client"""
        # Get service registry
        self._registry = self.app.get_component('service_registry')
        if not self._registry:
            raise RuntimeError("Service registry not available")
            
        # Register service if configured
        service_info = self.config.get('service', {})
        if service_info:
            await self.register_service(
                service_info.get('name'),
                service_info.get('url'),
                service_info.get('metadata')
            )
            
        # Start heartbeat task
        if self._instance_id:
            self.add_cleanup_task(
                asyncio.create_task(self._heartbeat())
            )

    async def cleanup(self) -> None:
        """Cleanup client resources"""
        # Deregister service
        if self._instance_id:
            await self._registry.deregister_service(
                self._instance_id
            )
            
        self._cache.clear()
        self._watchers.clear()

    @handle_errors(logger=None)
    async def register_service(self,
                             name: str,
                             url: str,
                             metadata: Optional[Dict] = None) -> None:
        """Register service with registry"""
        self._instance_id = await self._registry.register_service(
            name,
            url,
            metadata
        )

    @handle_errors(logger=None)
    async def get_service(self,
                         name: str,
                         metadata: Optional[Dict] = None,
                         strategy: str = None) -> Optional[Dict]:
        """Get service instance"""
        # Check cache
        cache_key = self._get_cache_key(name, metadata)
        cached = self._cache.get(cache_key)
        
        if cached and self._is_cache_valid(cached):
            instances = cached['instances']
        else:
            # Get from registry
            services = await self._registry.get_services(
                name,
                metadata
            )
            
            if not services:
                return None
                
            instances = services[0]['instances']
            
            # Update cache
            self._cache[cache_key] = {
                'instances': instances,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        if not instances:
            return None
            
        # Select instance
        strategy = strategy or self._load_balancer
        return self._select_instance(instances, strategy)

    async def watch_service(self,
                          name: str,
                          callback: Callable) -> None:
        """Watch service for changes"""
        if name not in self._watchers:
            self._watchers[name] = []
            
            # Register watcher with registry
            await self._registry.watch_service(
                name,
                self._handle_service_event
            )
            
        self._watchers[name].append(callback)

    async def unwatch_service(self,
                            name: str,
                            callback: Callable) -> None:
        """Remove service watcher"""
        if name in self._watchers:
            self._watchers[name].remove(callback)
            
            if not self._watchers[name]:
                del self._watchers[name]

    def _select_instance(self,
                        instances: List[Dict],
                        strategy: str) -> Dict:
        """Select service instance using strategy"""
        # Filter healthy instances
        healthy = [
            i for i in instances
            if i['status'] == 'healthy'
        ]
        
        if not healthy:
            healthy = instances
            
        if strategy == 'random':
            return random.choice(healthy)
        elif strategy == 'least_conn':
            return min(
                healthy,
                key=lambda i: i.get('connections', 0)
            )
        else:  # round_robin
            return healthy[0]

    def _get_cache_key(self,
                      name: str,
                      metadata: Optional[Dict]) -> str:
        """Generate cache key"""
        if not metadata:
            return name
            
        metadata_str = json.dumps(
            metadata,
            sort_keys=True
        )
        return f"{name}:{metadata_str}"

    def _is_cache_valid(self, cached: Dict) -> bool:
        """Check if cache entry is valid"""
        now = datetime.utcnow()
        timestamp = datetime.fromisoformat(cached['timestamp'])
        return (now - timestamp).total_seconds() < self._cache_ttl

    async def _heartbeat(self) -> None:
        """Send periodic heartbeat"""
        while True:
            try:
                await asyncio.sleep(self._heartbeat_interval)
                
                if self._instance_id:
                    await self._registry.heartbeat(
                        self._instance_id
                    )
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Heartbeat failed: {str(e)}")
                await asyncio.sleep(5)

    async def _handle_service_event(self,
                                  event: Dict) -> None:
        """Handle service events"""
        service = event['service']
        
        if service in self._watchers:
            # Clear cache
            for key in list(self._cache.keys()):
                if key.startswith(f"{service}:"):
                    del self._cache[key]
                    
            # Notify watchers
            for callback in self._watchers[service]:
                try:
                    await callback(event)
                except Exception as e:
                    self.logger.error(
                        f"Watcher callback failed: {str(e)}"
                    ) 