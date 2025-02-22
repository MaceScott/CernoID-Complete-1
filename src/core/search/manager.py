from typing import Dict, Optional, Any, List, Union, Type
import asyncio
from datetime import datetime
import importlib
from ..base import BaseComponent
from ..utils.errors import handle_errors, SearchError

class SearchManager(BaseComponent):
    """Advanced search management system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._engines: Dict[str, Any] = {}
        self._indices: Dict[str, 'Index'] = {}
        self._analyzers: Dict[str, 'Analyzer'] = {}
        self._default = self.config.get('search.default', 'memory')
        self._batch_size = self.config.get('search.batch_size', 100)
        self._refresh_interval = self.config.get('search.refresh_interval', 60)
        self._connection_pool = None
        self._stats = {
            'indexed': 0,
            'searched': 0,
            'updated': 0,
            'deleted': 0
        }

    async def initialize(self) -> None:
        """Initialize search manager"""
        try:
            # Load search configurations
            engines = self.config.get('search.engines', {})
            for name, config in engines.items():
                await self.add_engine(name, config)
            
            # Initialize connection pool
            self._connection_pool = await self._create_pool()
            
            # Start background tasks
            self._start_background_tasks()
            
        except Exception as e:
            raise SearchError(f"Search initialization failed: {str(e)}")

    async def cleanup(self) -> None:
        """Cleanup search resources"""
        try:
            # Close all engines
            for engine in self._engines.values():
                await engine.cleanup()
            
            # Close connection pool
            if self._connection_pool:
                await self._connection_pool.close()
                
            self._engines.clear()
            self._indices.clear()
            self._analyzers.clear()
            
        except Exception as e:
            self.logger.error(f"Search cleanup error: {str(e)}")

    @handle_errors(logger=None)
    async def add_engine(self,
                        name: str,
                        config: Dict) -> bool:
        """Add search engine"""
        try:
            # Get engine type
            engine_type = config.get('type', 'memory')
            
            # Import engine module
            module = importlib.import_module(
                f".engines.{engine_type}",
                package="core.search"
            )
            
            # Create engine
            engine = await module.create_engine(
                config,
                self._connection_pool
            )
            self._engines[name] = engine
            
            return True
            
        except Exception as e:
            raise SearchError(f"Engine creation failed: {str(e)}")

    @handle_errors(logger=None)
    async def create_index(self,
                         name: str,
                         schema: Dict,
                         engine: Optional[str] = None) -> 'Index':
        """Create search index"""
        try:
            # Get engine
            search_engine = self._get_engine(engine)
            
            # Create index
            index = await search_engine.create_index(name, schema)
            self._indices[name] = index
            
            return index
            
        except Exception as e:
            raise SearchError(f"Index creation failed: {str(e)}")

    @handle_errors(logger=None)
    async def index(self,
                   index: str,
                   documents: List[Dict],
                   engine: Optional[str] = None) -> bool:
        """Index documents"""
        try:
            # Get engine
            search_engine = self._get_engine(engine)
            
            # Process in batches
            for i in range(0, len(documents), self._batch_size):
                batch = documents[i:i + self._batch_size]
                await search_engine.index(index, batch)
                self._stats['indexed'] += len(batch)
            
            return True
            
        except Exception as e:
            raise SearchError(f"Indexing failed: {str(e)}")

    @handle_errors(logger=None)
    async def search(self,
                    index: str,
                    query: Union[str, Dict],
                    options: Optional[Dict] = None,
                    engine: Optional[str] = None) -> Dict:
        """Search documents"""
        try:
            # Get engine
            search_engine = self._get_engine(engine)
            
            # Execute search
            async with self._connection_pool.acquire() as conn:
                results = await search_engine.search(
                    index,
                    query,
                    options or {},
                    connection=conn
                )
            
            self._stats['searched'] += 1
            return results
            
        except Exception as e:
            raise SearchError(f"Search failed: {str(e)}")

    async def update(self,
                    index: str,
                    document_id: str,
                    document: Dict,
                    engine: Optional[str] = None) -> bool:
        """Update document"""
        try:
            # Get engine
            search_engine = self._get_engine(engine)
            
            # Update document
            success = await search_engine.update(
                index,
                document_id,
                document
            )
            
            if success:
                self._stats['updated'] += 1
            
            return success
            
        except Exception as e:
            raise SearchError(f"Update failed: {str(e)}")

    async def delete(self,
                    index: str,
                    document_id: str,
                    engine: Optional[str] = None) -> bool:
        """Delete document"""
        try:
            # Get engine
            search_engine = self._get_engine(engine)
            
            # Delete document
            success = await search_engine.delete(index, document_id)
            
            if success:
                self._stats['deleted'] += 1
            
            return success
            
        except Exception as e:
            raise SearchError(f"Deletion failed: {str(e)}")

    async def get_stats(self) -> Dict[str, Any]:
        """Get search statistics"""
        stats = self._stats.copy()
        
        # Add engine stats
        stats['engines'] = {
            name: await engine.get_stats()
            for name, engine in self._engines.items()
        }
        
        return stats

    def _get_engine(self, name: Optional[str] = None) -> Any:
        """Get search engine"""
        name = name or self._default
        if name not in self._engines:
            raise SearchError(f"Unknown search engine: {name}")
        return self._engines[name]

    async def _create_pool(self) -> Any:
        """Create connection pool"""
        try:
            from .pool import SearchConnectionPool
            return await SearchConnectionPool.create(
                self.config.get('search.pool', {})
            )
        except Exception as e:
            raise SearchError(f"Pool creation failed: {str(e)}")

    def _start_background_tasks(self) -> None:
        """Start background tasks"""
        asyncio.create_task(self._refresh_task())
        asyncio.create_task(self._cleanup_task())

    async def _refresh_task(self) -> None:
        """Refresh indices periodically"""
        while True:
            try:
                for engine in self._engines.values():
                    await engine.refresh()
                await asyncio.sleep(self._refresh_interval)
            except Exception as e:
                self.logger.error(f"Refresh error: {str(e)}")
                await asyncio.sleep(self._refresh_interval)

    async def _cleanup_task(self) -> None:
        """Cleanup expired documents"""
        while True:
            try:
                for engine in self._engines.values():
                    await engine.cleanup()
                await asyncio.sleep(3600)  # Run hourly
            except Exception as e:
                self.logger.error(f"Cleanup error: {str(e)}")
                await asyncio.sleep(3600) 