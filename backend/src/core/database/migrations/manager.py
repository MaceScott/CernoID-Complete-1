from typing import List, Dict, Any
import asyncio
from pathlib import Path
import importlib.util
import logging
from datetime import datetime

class MigrationManager:
    """Database migration management system"""
    
    def __init__(self, migrations_dir: Path):
        self.migrations_dir = migrations_dir
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger('MigrationManager')
        self._migrations: Dict[str, Any] = {}

    async def run_migrations(self) -> None:
        """Run all pending migrations"""
        try:
            # Load migrations
            await self._load_migrations()
            
            # Get current migration state
            current_version = await self._get_current_version()
            
            # Run pending migrations
            for version, migration in sorted(self._migrations.items()):
                if version > current_version:
                    self.logger.info(f"Running migration: {version}")
                    await migration.up()
                    await self._update_version(version)
                    
            self.logger.info("Migrations completed successfully")
            
        except Exception as e:
            self.logger.error(f"Migration failed: {str(e)}")
            raise

    async def _load_migrations(self) -> None:
        """Load migration files"""
        try:
            for file_path in sorted(self.migrations_dir.glob('*.py')):
                if file_path.name.startswith('__'):
                    continue

                spec = importlib.util.spec_from_file_location(
                    file_path.stem, file_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                if hasattr(module, 'Migration'):
                    version = file_path.stem.split('_')[0]
                    self._migrations[version] = module.Migration()
                    self.logger.info(f"Loaded migration: {version}")
        except Exception as e:
            self.logger.error(f"Failed to load migrations: {str(e)}")
            raise

    async def _get_current_version(self) -> str:
        """Get current migration version"""
        from core.database.models import MigrationHistory
        
        async with self.db.session() as session:
            result = await session.query(MigrationHistory)\
                .order_by(MigrationHistory.version.desc())\
                .first()
            return result.version if result else '0'

    async def _update_version(self, version: str) -> None:
        """Update migration version"""
        from core.database.models import MigrationHistory
        
        async with self.db.session() as session:
            migration = MigrationHistory(
                version=version,
                applied_at=datetime.utcnow()
            )
            session.add(migration)
            await session.commit() 