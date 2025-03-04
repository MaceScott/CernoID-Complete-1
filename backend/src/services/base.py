"""
Base service class with common functionality.
"""
from typing import Optional, Any
from core.database.session import get_db_session
from core.utils.errors import handle_exceptions
import logging

class BaseService:
    """Base class for all services"""
    
    def __init__(self):
        self.db = get_db_session()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
    
    async def cleanup(self):
        """Cleanup resources"""
        pass
    
    @handle_exceptions()
    async def get_by_id(self, model: str, id: Any) -> Optional[Any]:
        """Generic get by ID method"""
        return await getattr(self.db, model).get(id) 