from typing import List, Dict, Any
import asyncio
from pathlib import Path
import importlib.util
import logging
from datetime import datetime
import subprocess
import os

class MigrationManager:
    """Database migration management system using Alembic"""
    
    def __init__(self, migrations_dir: Path):
        self.migrations_dir = migrations_dir
        self.logger = logging.getLogger('MigrationManager')

    async def run_migrations(self) -> None:
        """Run all pending migrations using Alembic"""
        try:
            # Change to the directory containing alembic.ini
            os.chdir(str(self.migrations_dir.parent))
            
            # Run Alembic upgrade
            result = subprocess.run(['alembic', 'upgrade', 'head'], 
                                 capture_output=True, 
                                 text=True)
            
            if result.returncode == 0:
                self.logger.info("Migrations completed successfully")
            else:
                error_msg = result.stderr or result.stdout
                self.logger.error(f"Migration failed: {error_msg}")
                raise Exception(f"Migration failed: {error_msg}")
            
        except Exception as e:
            self.logger.error(f"Migration failed: {str(e)}")
            raise 