from typing import Optional, Dict
import asyncio
from datetime import datetime
import subprocess
import shutil
from pathlib import Path
import gzip
import logging

class DatabaseBackup:
    """Database backup and recovery system"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.backup_path = Path(config['backup_path'])
        self.backup_path.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger('DatabaseBackup')
        self._setup_logger()

    async def create_backup(self, backup_name: Optional[str] = None) -> Path:
        """Create database backup"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = backup_name or f"backup_{timestamp}"
            backup_file = self.backup_path / f"{backup_name}.sql.gz"

            # Create backup command
            cmd = [
                'pg_dump',
                f"--dbname={self.config['url']}",
                '--format=plain',
                '--no-owner',
                '--no-acl'
            ]

            # Execute backup
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Compress backup
            data, err = await process.communicate()
            if process.returncode != 0:
                raise Exception(f"Backup failed: {err.decode()}")

            # Save compressed backup
            with gzip.open(backup_file, 'wb') as f:
                f.write(data)

            self.logger.info(f"Backup created: {backup_file}")
            return backup_file

        except Exception as e:
            self.logger.error(f"Backup creation failed: {str(e)}")
            raise

    async def restore_backup(self, backup_file: Path) -> bool:
        """Restore database from backup"""
        try:
            if not backup_file.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_file}")

            # Decompress backup
            with gzip.open(backup_file, 'rb') as f:
                data = f.read()

            # Restore command
            cmd = [
                'psql',
                f"--dbname={self.config['url']}",
                '--single-transaction'
            ]

            # Execute restore
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Send backup data
            stdout, stderr = await process.communicate(input=data)
            if process.returncode != 0:
                raise Exception(f"Restore failed: {stderr.decode()}")

            self.logger.info(f"Backup restored: {backup_file}")
            return True

        except Exception as e:
            self.logger.error(f"Backup restoration failed: {str(e)}")
            raise

    async def cleanup_old_backups(self, keep_days: int = 30) -> None:
        """Clean up old backup files"""
        try:
            cutoff_date = datetime.now().timestamp() - (keep_days * 86400)
            
            for backup_file in self.backup_path.glob('*.sql.gz'):
                if backup_file.stat().st_mtime < cutoff_date:
                    backup_file.unlink()
                    self.logger.info(f"Removed old backup: {backup_file}")

            self.logger.info("Old backups cleanup completed successfully.")

        except Exception as e:
            self.logger.error(f"Backup cleanup failed: {str(e)}")
            raise

    def _setup_logger(self) -> None:
        """Setup backup logger"""
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO) 