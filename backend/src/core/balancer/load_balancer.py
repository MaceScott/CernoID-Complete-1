from typing import Dict, List, Optional, Any, Tuple
import asyncio
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import random
import statistics
from collections import defaultdict
import aiohttp

@dataclass
class ServiceEndpoint:
    """Service endpoint information"""
    host: str
    port: int
    weight: int = 100
    max_fails: int = 3
    fail_timeout: int = 30
    current_fails: int = 0
    last_fail_time: Optional[datetime] = None
    response_times: List[float] = None
    active_connections: int = 0

class LoadBalancer:
    """Advanced load balancing system"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger('LoadBalancer')
        self._endpoints: Dict[str, List[ServiceEndpoint]] = {}
        self._strategies = {
            'round_robin': self._round_robin,
            'weighted_round_robin': self._weighted_round_robin,
            'least_connections': self._least_connections,
            'least_response_time': self._least_response_time,
            'ip_hash': self._ip_hash
        }
        self._current_index: Dict[str, int] = defaultdict(int)
        self._session: Optional[aiohttp.ClientSession] = None
        self._health_check_task: Optional[asyncio.Task] = None

    async def initialize(self) -> None:
        """Initialize load balancer"""
        try:
            self._session = aiohttp.ClientSession()
            
            # Start health checks if enabled
            if self.config.get('enable_health_checks', True):
                self._health_check_task = asyncio.create_task(
                    self._check_endpoints_health()
                )
                
            self.logger.info("Load balancer initialized")
            
        except Exception as e:
            self.logger.error(f"Load balancer initialization failed: {str(e)}")
            raise

    def add_endpoint(self,
                    service: str,
                    endpoint: ServiceEndpoint) -> None:
        """Add service endpoint"""
        if service not in self._endpoints:
            self._endpoints[service] = []
            
        endpoint.response_times = []
        self._endpoints[service].append(endpoint)
        self.logger.info(f"Added endpoint for service {service}")

    def remove_endpoint(self,
                       service: str,
                       host: str,
                       port: int) -> None:
        """Remove service endpoint"""
        if service in self._endpoints:
            self._endpoints[service] = [
                ep for ep in self._endpoints[service]
                if not (ep.host == host and ep.port == port)
            ]
            self.logger.info(f"Removed endpoint for service {service}")

    async def get_endpoint(self,
                          service: str,
                          strategy: str = 'round_robin',
                          client_ip: Optional[str] = None) -> Optional[ServiceEndpoint]:
        """Get service endpoint using specified strategy"""
        try:
            if service not in self._endpoints:
                return None
                
            # Filter out failed endpoints
            available_endpoints = [
                ep for ep in self._endpoints[service]
                if self._is_endpoint_available(ep)
            ]
            
            if not available_endpoints:
                return None
                
            # Use specified strategy
            strategy_func = self._strategies.get(
                strategy,
                self._round_robin
            )
            
            endpoint = await strategy_func(
                available_endpoints,
                service,
                client_ip
            )
            
            if endpoint:
                endpoint.active_connections += 1
                
            return endpoint
            
        except Exception as e:
            self.logger.error(f"Endpoint selection failed: {str(e)}")
            return None

    async def release_endpoint(self,
                             service: str,
                             endpoint: ServiceEndpoint,
                             response_time: Optional[float] = None) -> None:
        """Release endpoint and update metrics"""
        try:
            endpoint.active_connections -= 1
            
            if response_time is not None:
                endpoint.response_times.append(response_time)
                # Keep last N response times
                max_samples = self.config.get('response_time_samples', 100)
                if len(endpoint.response_times) > max_samples:
                    endpoint.response_times = endpoint.response_times[-max_samples:]
                    
        except Exception as e:
            self.logger.error(f"Endpoint release failed: {str(e)}")

    async def mark_endpoint_failed(self,
                                 service: str,
                                 endpoint: ServiceEndpoint) -> None:
        """Mark endpoint as failed"""
        try:
            endpoint.current_fails += 1
            endpoint.last_fail_time = datetime.utcnow()
            
            if endpoint.current_fails >= endpoint.max_fails:
                self.logger.warning(
                    f"Endpoint {endpoint.host}:{endpoint.port} "
                    f"marked as failed"
                )
                
        except Exception as e:
            self.logger.error(f"Endpoint failure marking failed: {str(e)}")

    async def cleanup(self) -> None:
        """Cleanup load balancer resources"""
        try:
            if self._health_check_task:
                self._health_check_task.cancel()
                
            if self._session:
                await self._session.close()
                
            self.logger.info("Load balancer cleaned up")
            
        except Exception as e:
            self.logger.error(f"Load balancer cleanup failed: {str(e)}")

    def _is_endpoint_available(self, endpoint: ServiceEndpoint) -> bool:
        """Check if endpoint is available"""
        if endpoint.current_fails >= endpoint.max_fails:
            if endpoint.last_fail_time:
                if datetime.utcnow() - endpoint.last_fail_time < \
                   timedelta(seconds=endpoint.fail_timeout):
                    return False
                # Reset fails after timeout
                endpoint.current_fails = 0
                
        return True

    async def _round_robin(self,
                          endpoints: List[ServiceEndpoint],
                          service: str,
                          _: Optional[str] = None) -> Optional[ServiceEndpoint]:
        """Round-robin selection strategy"""
        if not endpoints:
            return None
            
        index = self._current_index[service]
        self._current_index[service] = (index + 1) % len(endpoints)
        return endpoints[index]

    async def _weighted_round_robin(self,
                                  endpoints: List[ServiceEndpoint],
                                  _: str,
                                  __: Optional[str] = None) -> Optional[ServiceEndpoint]:
        """Weighted round-robin selection strategy"""
        if not endpoints:
            return None
            
        total_weight = sum(ep.weight for ep in endpoints)
        if total_weight == 0:
            return random.choice(endpoints)
            
        point = random.randint(0, total_weight - 1)
        for endpoint in endpoints:
            if point < endpoint.weight:
                return endpoint
            point -= endpoint.weight
            
        return endpoints[-1]

    async def _least_connections(self,
                               endpoints: List[ServiceEndpoint],
                               _: str,
                               __: Optional[str] = None) -> Optional[ServiceEndpoint]:
        """Least connections selection strategy"""
        if not endpoints:
            return None
            
        return min(
            endpoints,
            key=lambda ep: ep.active_connections
        )

    async def _least_response_time(self,
                                 endpoints: List[ServiceEndpoint],
                                 _: str,
                                 __: Optional[str] = None) -> Optional[ServiceEndpoint]:
        """Least response time selection strategy"""
        if not endpoints:
            return None
            
        # Calculate average response times
        avg_times = []
        for endpoint in endpoints:
            if endpoint.response_times:
                avg = statistics.mean(endpoint.response_times)
            else:
                avg = float('inf')
            avg_times.append((endpoint, avg))
            
        return min(avg_times, key=lambda x: x[1])[0]

    async def _ip_hash(self,
                      endpoints: List[ServiceEndpoint],
                      _: str,
                      client_ip: Optional[str] = None) -> Optional[ServiceEndpoint]:
        """IP hash selection strategy"""
        if not endpoints or not client_ip:
            return await self._round_robin(endpoints, _)
            
        hash_value = sum(ord(c) for c in client_ip)
        return endpoints[hash_value % len(endpoints)]

    async def _check_endpoints_health(self) -> None:
        """Periodic health check of endpoints"""
        while True:
            try:
                for service, endpoints in self._endpoints.items():
                    for endpoint in endpoints:
                        try:
                            url = f"http://{endpoint.host}:{endpoint.port}/health"
                            async with self._session.get(
                                url,
                                timeout=5
                            ) as response:
                                if response.status == 200:
                                    endpoint.current_fails = 0
                                else:
                                    await self.mark_endpoint_failed(
                                        service,
                                        endpoint
                                    )
                        except Exception:
                            await self.mark_endpoint_failed(service, endpoint)
                            
                await asyncio.sleep(
                    self.config.get('health_check_interval', 30)
                )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check failed: {str(e)}")
                await asyncio.sleep(5) 