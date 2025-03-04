from typing import Optional, Dict, Any, Union
import aiohttp
import json
from ..base import BaseComponent
from ..utils.errors import handle_errors

class TestClient(BaseComponent):
    """API testing client"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._base_url = self.config.get('test.base_url', 'http://localhost:8000')
        self._timeout = self.config.get('test.timeout', 30)
        self._session: Optional[aiohttp.ClientSession] = None
        self._headers: Dict[str, str] = {}

    async def initialize(self) -> None:
        """Initialize test client"""
        self._session = aiohttp.ClientSession(
            base_url=self._base_url,
            timeout=aiohttp.ClientTimeout(total=self._timeout)
        )

    async def cleanup(self) -> None:
        """Cleanup test client resources"""
        if self._session:
            await self._session.close()
        self._headers.clear()

    def set_token(self, token: str) -> None:
        """Set authentication token"""
        self._headers['Authorization'] = f"Bearer {token}"

    def set_api_key(self, api_key: str) -> None:
        """Set API key"""
        self._headers['X-API-Key'] = api_key

    @handle_errors(logger=None)
    async def get(self,
                 path: str,
                 params: Optional[Dict] = None) -> Dict[str, Any]:
        """Send GET request"""
        async with self._session.get(
            path,
            params=params,
            headers=self._headers
        ) as response:
            return await self._handle_response(response)

    @handle_errors(logger=None)
    async def post(self,
                  path: str,
                  data: Optional[Dict] = None) -> Dict[str, Any]:
        """Send POST request"""
        async with self._session.post(
            path,
            json=data,
            headers=self._headers
        ) as response:
            return await self._handle_response(response)

    @handle_errors(logger=None)
    async def put(self,
                 path: str,
                 data: Optional[Dict] = None) -> Dict[str, Any]:
        """Send PUT request"""
        async with self._session.put(
            path,
            json=data,
            headers=self._headers
        ) as response:
            return await self._handle_response(response)

    @handle_errors(logger=None)
    async def delete(self,
                    path: str,
                    params: Optional[Dict] = None) -> Dict[str, Any]:
        """Send DELETE request"""
        async with self._session.delete(
            path,
            params=params,
            headers=self._headers
        ) as response:
            return await self._handle_response(response)

    async def _handle_response(self,
                             response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Handle API response"""
        content_type = response.headers.get('Content-Type', '')
        
        if 'application/json' in content_type:
            data = await response.json()
        else:
            data = await response.text()
            
        if not response.ok:
            raise Exception(
                f"Request failed: {response.status} - {data}"
            )
            
        return data 