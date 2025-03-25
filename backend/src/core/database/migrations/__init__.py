"""
Database migrations module.
"""

import os
import logging
from typing import Optional
from alembic import command
from alembic.config import Config as AlembicConfig

from ..base import Base
from ...utils.config import Config

logger = logging.getLogger(__name__)

def run_migrations(config: Optional[Config] = None) -> None:
    """
    Run database migrations using Alembic.
    
    Args:
        config: Optional configuration object.
    """
    try:
        # Get the alembic.ini file path
        alembic_ini = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'alembic.ini')
        
        if not os.path.exists(alembic_ini):
            raise FileNotFoundError(f"Alembic config file not found at {alembic_ini}")
        
        # Create Alembic config
        alembic_cfg = AlembicConfig(alembic_ini)
        
        # Run migrations
        logger.info("Running database migrations...")
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to run database migrations: {str(e)}")
        raise 