from typing import Dict, Optional, Any, List, Union
import asyncio
from datetime import datetime
import importlib
from ..base import BaseComponent
from ..utils.errors import handle_errors

class DatabaseManager(BaseComponent):
    """Advanced database management system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._connections: Dict[str, Any] = {}
        self._pools: Dict[str, Any] = {}
        self._models: Dict[str, Any] = {}
        self._migrations: Dict[str, Any] = {}
        self._default = self.config.get('database.default', 'default')
        self._auto_migrate = self.config.get('database.auto_migrate', True)
        self._pool_size = self.config.get('database.pool_size', 10)
        self._timeout = self.config.get('database.timeout', 30)
        self._stats = {
            'queries': 0,
            'transactions': 0,
            'errors': 0
        }

    async def initialize(self) -> None:
        """Initialize database manager"""
        databases = self.config.get('database.connections', {})

        for name, config in databases.items():
            await self.add_connection(name, config)
            self.logger.info(f"Database connection '{name}' initialized successfully.")

        if self._auto_migrate:
            await self.migrate()
            self.logger.info("Database migrations executed successfully.")

    async def cleanup(self) -> None:
        """Cleanup database resources"""
        # Close all connections
        for name in list(self._connections.keys()):
            await self.close_connection(name)
            
        self._connections.clear()
        self._pools.clear()
        self._models.clear()
        self._migrations.clear()

    @handle_errors(logger=None)
    async def add_connection(self,
                           name: str,
                           config: Dict) -> bool:
        """Add database connection"""
        try:
            # Get database type
            db_type = config.get('type', 'sqlite')
            
            # Import backend module
            module = importlib.import_module(
                f".backends.{db_type}",
                package="core.database"
            )
            
            # Create connection
            connection = await module.create_connection(
                config,
                pool_size=self._pool_size,
                timeout=self._timeout
            )
            
            # Store connection
            self._connections[name] = connection
            
            # Create connection pool if supported
            if hasattr(module, 'create_pool'):
                pool = await module.create_pool(
                    config,
                    pool_size=self._pool_size,
                    timeout=self._timeout
                )
                self._pools[name] = pool
                
            return True
            
        except Exception as e:
            self.logger.error(f"Database connection error: {str(e)}")
            self._stats['errors'] += 1
            return False

    async def close_connection(self, name: str) -> bool:
        """Close database connection"""
        try:
            # Close pool if exists
            if name in self._pools:
                await self._pools[name].close()
                del self._pools[name]
                
            # Close connection
            if name in self._connections:
                await self._connections[name].close()
                del self._connections[name]
                
            return True
            
        except Exception as e:
            self.logger.error(f"Connection close error: {str(e)}")
            return False

    def connection(self,
                  name: Optional[str] = None) -> Any:
        """Get database connection"""
        name = name or self._default
        if name not in self._connections:
            raise ValueError(f"Unknown connection: {name}")
        return self._connections[name]

    def pool(self,
            name: Optional[str] = None) -> Any:
        """Get connection pool"""
        name = name or self._default
        if name not in self._pools:
            raise ValueError(f"Unknown pool: {name}")
        return self._pools[name]

    @handle_errors(logger=None)
    async def execute(self,
                     query: str,
                     params: Optional[tuple] = None,
                     connection: Optional[str] = None) -> Any:
        """Execute database query"""
        try:
            conn = self.connection(connection)
            
            # Execute query
            result = await conn.execute(query, params or ())
            
            self._stats['queries'] += 1
            return result
            
        except Exception as e:
            self.logger.error(f"Query execution error: {str(e)}")
            self._stats['errors'] += 1
            raise

    async def transaction(self,
                         connection: Optional[str] = None) -> Any:
        """Start database transaction"""
        try:
            conn = self.connection(connection)
            
            # Start transaction
            transaction = await conn.transaction()
            
            self._stats['transactions'] += 1
            return transaction
            
        except Exception as e:
            self.logger.error(f"Transaction error: {str(e)}")
            self._stats['errors'] += 1
            raise

    async def migrate(self,
                     connection: Optional[str] = None) -> bool:
        """Run database migrations"""
        try:
            conn = self.connection(connection)
            
            # Run migrations
            for migration in self._migrations.values():
                await migration.run(conn)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Migration error: {str(e)}")
            return False

    def register_model(self,
                      name: str,
                      model: Any) -> None:
        """Register database model"""
        self._models[name] = model

    def get_model(self, name: str) -> Any:
        """Get registered model"""
        if name not in self._models:
            raise ValueError(f"Unknown model: {name}")
        return self._models[name]

    def register_migration(self,
                         name: str,
                         migration: Any) -> None:
        """Register database migration"""
        self._migrations[name] = migration

    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats = self._stats.copy()
        
        # Add connection stats
        stats['connections'] = {
            name: await conn.get_stats()
            for name, conn in self._connections.items()
        }
        
        return stats 