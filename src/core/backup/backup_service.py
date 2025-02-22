from typing import List
import asyncio
from datetime import datetime, timedelta
import aiofiles
import json
from pathlib import Path
from core.error_handling import handle_exceptions

class BackupService:
    def __init__(self):
        self.backup_path = Path("backups")
        self.backup_path.mkdir(exist_ok=True)
        self.retention_days = 30

    @handle_exceptions(logger=backup_logger.error)
    async def create_backup(self):
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backup_file = self.backup_path / f"backup_{timestamp}.json"

        # Backup database
        async with self.db_pool.acquire() as conn:
            tables = ['users', 'face_encodings', 'access_logs', 
                     'security_events', 'permissions']
            backup_data = {}
            
            for table in tables:
                records = await conn.fetch(f"SELECT * FROM {table}")
                backup_data[table] = [dict(record) for record in records]

        # Write backup file
        async with aiofiles.open(backup_file, 'w') as f:
            await f.write(json.dumps(backup_data, default=str))

        # Cleanup old backups
        await self._cleanup_old_backups()

    async def _cleanup_old_backups(self):
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
        for backup_file in self.backup_path.glob("backup_*.json"):
            file_date = datetime.strptime(
                backup_file.stem[7:], 
                '%Y%m%d_%H%M%S'
            )
            if file_date < cutoff_date:
                backup_file.unlink() 
