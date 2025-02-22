from typing import Dict, List, Optional, Any
import asyncio
from datetime import datetime
import importlib
from pathlib import Path
import re
from ..base import BaseComponent
from ..utils.errors import handle_errors

class MigrationManager(BaseComponent):
    """Database migration management system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._migrations: Dict[str, Dict] = {}
        self._migrations_path = Path(
            self.config.get('database.migrations_path', 'migrations')
        )
        self._schema_version = 0
        self._migration_table = self.config.get(
            'database.migration_table',
            'schema_migrations'
        )
        self._lock_timeout = self.config.get(
            'database.migration_lock_timeout',
            300
        )

    async def initialize(self) -> None:
        """Initialize migration manager"""
        self._migrations_path.mkdir(parents=True, exist_ok=True)
        
        # Ensure migration table exists
        await self._ensure_migration_table()
        
        # Load current schema version
        await self._load_schema_version()
        
        # Discover migrations
        await self._discover_migrations()

    async def cleanup(self) -> None:
        """Cleanup migration resources"""
        self._migrations.clear()

    @handle_errors(logger=None)
    async def create_migration(self,
                             name: str,
                             description: str = '') -> str:
        """Create new migration file"""
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        migration_id = f"{timestamp}_{name}"
        
        # Create migration file
        migration_file = self._migrations_path / f"{migration_id}.py"
        
        template = self._get_migration_template(
            migration_id,
            description
        )
        
        with open(migration_file, 'w') as f:
            f.write(template)
            
        return migration_id

    @handle_errors(logger=None)
    async def run_migrations(self,
                           target_version: Optional[int] = None) -> List[str]:
        """Run pending migrations"""
        # Acquire migration lock
        async with self._migration_lock():
            # Get pending migrations
            pending = await self._get_pending_migrations(target_version)
            
            if not pending:
                return []
                
            # Run migrations
            applied = []
            for migration_id in pending:
                try:
                    await self._run_migration(migration_id)
                    applied.append(migration_id)
                except Exception as e:
                    self.logger.error(
                        f"Migration failed {migration_id}: {str(e)}"
                    )
                    raise
                    
            return applied

    @handle_errors(logger=None)
    async def rollback_migrations(self,
                                steps: int = 1) -> List[str]:
        """Rollback migrations"""
        async with self._migration_lock():
            # Get migrations to rollback
            to_rollback = await self._get_rollback_migrations(steps)
            
            if not to_rollback:
                return []
                
            # Run rollbacks
            rolled_back = []
            for migration_id in to_rollback:
                try:
                    await self._rollback_migration(migration_id)
                    rolled_back.append(migration_id)
                except Exception as e:
                    self.logger.error(
                        f"Rollback failed {migration_id}: {str(e)}"
                    )
                    raise
                    
            return rolled_back

    async def get_status(self) -> Dict[str, Any]:
        """Get migration status"""
        return {
            'current_version': self._schema_version,
            'available_migrations': len(self._migrations),
            'pending_migrations': len(
                await self._get_pending_migrations()
            ),
            'migrations': [
                {
                    'id': mid,
                    'version': info['version'],
                    'name': info['name'],
                    'applied': info['version'] <= self._schema_version
                }
                for mid, info in self._migrations.items()
            ]
        }

    async def _ensure_migration_table(self) -> None:
        """Ensure migration tracking table exists"""
        db = self.app.get_component('database')
        if not db:
            raise RuntimeError("Database component not available")
            
        query = f"""
            CREATE TABLE IF NOT EXISTS {self._migration_table} (
                version INTEGER PRIMARY KEY,
                migration_id VARCHAR(255) NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        
        await db.execute(query)

    async def _load_schema_version(self) -> None:
        """Load current schema version"""
        db = self.app.get_component('database')
        if not db:
            raise RuntimeError("Database component not available")
            
        query = f"""
            SELECT MAX(version) as version 
            FROM {self._migration_table}
        """
        
        result = await db.fetch_one(query)
        if result and result['version'] is not None:
            self._schema_version = result['version']

    async def _discover_migrations(self) -> None:
        """Discover available migrations"""
        pattern = re.compile(r'^\d{14}_\w+\.py$')
        
        for file in sorted(self._migrations_path.glob('*.py')):
            if not pattern.match(file.name):
                continue
                
            migration_id = file.stem
            module_name = f"migrations.{migration_id}"
            
            try:
                spec = importlib.util.spec_from_file_location(
                    module_name,
                    file
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                version = int(migration_id.split('_')[0])
                name = migration_id.split('_', 1)[1]
                
                self._migrations[migration_id] = {
                    'version': version,
                    'name': name,
                    'module': module
                }
                
            except Exception as e:
                self.logger.error(
                    f"Failed to load migration {migration_id}: {str(e)}"
                )

    async def _get_pending_migrations(self,
                                    target_version: Optional[int] = None) -> List[str]:
        """Get pending migrations"""
        pending = []
        
        for mid, info in sorted(
            self._migrations.items(),
            key=lambda x: x[1]['version']
        ):
            if info['version'] > self._schema_version:
                if (target_version is None or 
                    info['version'] <= target_version):
                    pending.append(mid)
                    
        return pending

    async def _get_rollback_migrations(self,
                                     steps: int) -> List[str]:
        """Get migrations to rollback"""
        to_rollback = []
        
        for mid, info in sorted(
            self._migrations.items(),
            key=lambda x: x[1]['version'],
            reverse=True
        ):
            if info['version'] <= self._schema_version:
                to_rollback.append(mid)
                if len(to_rollback) >= steps:
                    break
                    
        return list(reversed(to_rollback))

    async def _run_migration(self, migration_id: str) -> None:
        """Run single migration"""
        migration = self._migrations[migration_id]
        module = migration['module']
        
        self.logger.info(f"Running migration: {migration_id}")
        
        db = self.app.get_component('database')
        async with db.transaction():
            # Run migration
            if hasattr(module, 'up'):
                await module.up(db)
                
            # Update schema version
            await db.execute(
                f"""
                INSERT INTO {self._migration_table} 
                (version, migration_id) 
                VALUES ($1, $2)
                """,
                migration['version'],
                migration_id
            )
            
        self._schema_version = migration['version']

    async def _rollback_migration(self, migration_id: str) -> None:
        """Rollback single migration"""
        migration = self._migrations[migration_id]
        module = migration['module']
        
        self.logger.info(f"Rolling back migration: {migration_id}")
        
        db = self.app.get_component('database')
        async with db.transaction():
            # Run rollback
            if hasattr(module, 'down'):
                await module.down(db)
                
            # Update schema version
            await db.execute(
                f"""
                DELETE FROM {self._migration_table}
                WHERE version = $1
                """,
                migration['version']
            )
            
        # Update schema version to previous migration
        await self._load_schema_version()

    def _get_migration_template(self,
                              migration_id: str,
                              description: str) -> str:
        """Get migration file template"""
        return f'''"""
{description}

Migration ID: {migration_id}
"""

async def up(db):
    """Apply migration"""
    await db.execute("""
        -- Add migration SQL here
    """)

async def down(db):
    """Rollback migration"""
    await db.execute("""
        -- Add rollback SQL here
    """)
'''

    async def _migration_lock(self):
        """Acquire migration lock"""
        db = self.app.get_component('database')
        if not db:
            raise RuntimeError("Database component not available")
            
        class MigrationLock:
            async def __aenter__(self):
                await db.execute(
                    "SELECT pg_advisory_lock($1)",
                    hash('migration_lock')
                )
                
            async def __aexit__(self, exc_type, exc, tb):
                await db.execute(
                    "SELECT pg_advisory_unlock($1)",
                    hash('migration_lock')
                )
                
        return MigrationLock() 