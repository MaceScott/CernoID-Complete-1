from typing import Dict, Optional, Any, List
from fastapi import Request, Response, HTTPException
import httpx
import asyncio
from datetime import datetime
import json
from ..base import BaseComponent
from ..utils.errors import handle_errors

class ReverseProxy(BaseComponent):
    """Advanced reverse proxy system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._upstreams: Dict[str, List[Dict]] = {}
        self._client = httpx.AsyncClient()
        self._timeout = self.config.get('proxy.timeout', 30)
        self._retry_attempts = self.config.get('proxy.retry_attempts', 3)
        self._health_interval = self.config.get('proxy.health_interval', 30)
        self._load_balancer = self.config.get('proxy.load_balancer', 'round_robin')
        self._sticky_sessions = self.config.get('proxy.sticky_sessions', False)
        self._session_cookie = self.config.get('proxy.session_cookie', 'PROXY_SESSION')

    async def initialize(self) -> None:
        """Initialize reverse proxy"""
        # Load upstream configurations
        await self._load_upstreams()
        
        # Start health checks
        if self._health_interval > 0:
            self.add_cleanup_task(
                asyncio.create_task(self._health_check())
            )

    async def cleanup(self) -> None:
        """Cleanup proxy resources"""
        await self._client.aclose()
        self._upstreams.clear()

    @handle_errors(logger=None)
    async def add_upstream(self,
                         name: str,
                         servers: List[Dict]) -> None:
        """Add upstream servers"""
        self._upstreams[name] = [
            {
                'url': server['url'].rstrip('/'),
                'weight': server.get('weight', 1),
                'status': 'unknown',
                'last_check': None,
                'failures': 0,
                'metadata': server.get('metadata', {})
            }
            for server in servers
        ]

    async def remove_upstream(self, name: str) -> None:
        """Remove upstream servers"""
        self._upstreams.pop(name, None)

    async def get_upstream_status(self,
                                name: Optional[str] = None) -> Dict:
        """Get upstream status"""
        if name:
            return {
                'name': name,
                'servers': self._upstreams.get(name, [])
            }
            
        return {
            name: servers
            for name, servers in self._upstreams.items()
        }

    @handle_errors(logger=None)
    async def handle_request(self,
                           request: Request,
                           upstream: str) -> Response:
        """Handle proxy request"""
        # Get upstream servers
        servers = self._upstreams.get(upstream)
        if not servers:
            raise HTTPException(status_code=503)
            
        # Get target server
        server = await self._get_server(request, servers)
        if not server:
            raise HTTPException(status_code=503)
            
        # Forward request
        try:
            response = await self._forward_request(
                request,
                server
            )
            return response
            
        except Exception as e:
            self.logger.error(f"Proxy request failed: {str(e)}")
            raise HTTPException(status_code=502)

    async def _get_server(self,
                         request: Request,
                         servers: List[Dict]) -> Optional[Dict]:
        """Get target server using load balancing"""
        # Filter healthy servers
        healthy = [
            s for s in servers
            if s['status'] != 'failed'
        ]
        
        if not healthy:
            return None
            
        # Check sticky session
        if self._sticky_sessions:
            session_id = request.cookies.get(self._session_cookie)
            if session_id:
                for server in healthy:
                    if (hash(server['url']) ==
                        int(session_id)):
                        return server
                        
        # Apply load balancing
        if self._load_balancer == 'random':
            return random.choice(healthy)
        elif self._load_balancer == 'least_conn':
            return min(
                healthy,
                key=lambda s: s.get('connections', 0)
            )
        else:  # round_robin
            return healthy[0]

    async def _forward_request(self,
                             request: Request,
                             server: Dict) -> Response:
        """Forward request to upstream server"""
        # Get request content
        body = await request.body()
        
        # Prepare headers
        headers = dict(request.headers)
        headers['X-Forwarded-For'] = request.client.host
        headers['X-Real-IP'] = request.client.host
        
        url = f"{server['url']}{request.url.path}"
        
        for attempt in range(self._retry_attempts):
            try:
                # Update connections
                server['connections'] = (
                    server.get('connections', 0) + 1
                )
                
                # Send request
                response = await self._client.request(
                    request.method,
                    url,
                    content=body,
                    headers=headers,
                    params=request.query_params,
                    timeout=self._timeout,
                    follow_redirects=True
                )
                
                # Update server status
                server['status'] = 'healthy'
                server['failures'] = 0
                
                # Create response
                proxy_response = Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
                
                # Add session cookie if needed
                if self._sticky_sessions:
                    proxy_response.set_cookie(
                        self._session_cookie,
                        str(hash(server['url']))
                    )
                    
                return proxy_response
                
            except Exception as e:
                server['failures'] += 1
                
                if (server['failures'] >= 3):
                    server['status'] = 'failed'
                    
                if attempt == self._retry_attempts - 1:
                    raise e
                    
                await asyncio.sleep(1)
                
            finally:
                # Update connections
                server['connections'] = (
                    server.get('connections', 0) - 1
                )

    async def _health_check(self) -> None:
        """Perform upstream health checks"""
        while True:
            try:
                await asyncio.sleep(self._health_interval)
                
                for servers in self._upstreams.values():
                    for server in servers:
                        try:
                            # Check server health
                            response = await self._client.get(
                                f"{server['url']}/health",
                                timeout=5
                            )
                            
                            if response.status_code == 200:
                                server['status'] = 'healthy'
                                server['failures'] = 0
                            else:
                                server['failures'] += 1
                                
                        except Exception:
                            server['failures'] += 1
                            
                        # Update status
                        if server['failures'] >= 3:
                            server['status'] = 'failed'
                            
                        server['last_check'] = (
                            datetime.utcnow().isoformat()
                        )
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check failed: {str(e)}")
                await asyncio.sleep(5)

    async def _load_upstreams(self) -> None:
        """Load upstream configurations"""
        try:
            config = self.app.get_component('config_manager')
            if not config:
                return
                
            upstreams = config.get('proxy.upstreams', [])
            for upstream in upstreams:
                await self.add_upstream(
                    upstream['name'],
                    upstream['servers']
                )
                
        except Exception as e:
            self.logger.error(f"Failed to load upstreams: {str(e)}") 