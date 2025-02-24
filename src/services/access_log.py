"""
Access log service implementation.
Handles business logic for access logging and retrieval.
"""

from typing import List, Optional, Dict
from datetime import datetime, timedelta
import logging
from core.utils.errors import handle_errors
from core.database.session import get_db_session
from api.schemas import AccessLog, AccessLogFilter, PaginatedResponse

logger = logging.getLogger(__name__)

class AccessLogService:
    def __init__(self):
        self.db = get_db_session()

    @handle_errors
    async def log_access(self,
                        person_id: Optional[int],
                        access_point: str,
                        access_type: str,
                        success: bool,
                        confidence: Optional[float] = None,
                        metadata: Optional[Dict] = None) -> AccessLog:
        """
        Create new access log entry
        
        Args:
            person_id: ID of person accessing (if identified)
            access_point: Location or device ID
            access_type: Type of access (entry/exit)
            success: Whether access was granted
            confidence: Recognition confidence if applicable
            metadata: Additional log information
            
        Returns:
            Created access log entry
        """
        async with self.db.transaction():
            # Get person name if ID provided
            person_name = None
            if person_id:
                person = await self.db.person.get(person_id)
                person_name = person.name if person else None

            # Create log entry
            log_entry = await self.db.access_log.create(
                person_id=person_id,
                person_name=person_name,
                access_point=access_point,
                access_type=access_type,
                access_time=datetime.utcnow(),
                success=success,
                confidence=confidence,
                metadata=metadata or {}
            )

            logger.info(
                f"Access {'granted' if success else 'denied'} for "
                f"{'person ' + str(person_id) if person_id else 'unknown person'} "
                f"at {access_point}"
            )

            return AccessLog.from_orm(log_entry)

    @handle_errors
    async def get_logs(self,
                      filter_params: AccessLogFilter,
                      page: int = 1,
                      page_size: int = 50) -> PaginatedResponse:
        """
        Get access logs with filtering and pagination
        
        Args:
            filter_params: Filter criteria
            page: Page number
            page_size: Items per page
            
        Returns:
            Paginated list of access logs
        """
        # Build query filters
        filters = {}
        if filter_params.person_id:
            filters["person_id"] = filter_params.person_id
        if filter_params.access_point:
            filters["access_point"] = filter_params.access_point
        if filter_params.success is not None:
            filters["success"] = filter_params.success
        if filter_params.start_date:
            filters["access_time__gte"] = filter_params.start_date
        if filter_params.end_date:
            filters["access_time__lte"] = filter_params.end_date

        # Get total count
        total = await self.db.access_log.count(filters)
        
        # Calculate pagination
        total_pages = (total + page_size - 1) // page_size
        offset = (page - 1) * page_size

        # Get logs
        logs = await self.db.access_log.get_many(
            filters=filters,
            limit=page_size,
            offset=offset,
            order_by=["-access_time"]
        )

        return PaginatedResponse(
            items=[AccessLog.from_orm(log) for log in logs],
            total=total,
            page=page,
            pages=total_pages,
            per_page=page_size
        )

    @handle_errors
    async def get_access_stats(self,
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> Dict:
        """
        Get access statistics for time period
        
        Args:
            start_date: Start of period
            end_date: End of period
            
        Returns:
            Dictionary of access statistics
        """
        filters = {}
        if start_date:
            filters["access_time__gte"] = start_date
        if end_date:
            filters["access_time__lte"] = end_date

        # Get basic stats
        total_accesses = await self.db.access_log.count(filters)
        successful_accesses = await self.db.access_log.count(
            {**filters, "success": True}
        )
        unique_persons = await self.db.access_log.count_distinct(
            "person_id",
            filters
        )

        # Get access points stats
        access_points = await self.db.access_log.group_by(
            "access_point",
            filters,
            ["count(*) as total"]
        )

        return {
            "total_accesses": total_accesses,
            "successful_accesses": successful_accesses,
            "failed_accesses": total_accesses - successful_accesses,
            "unique_persons": unique_persons,
            "access_points": {
                ap["access_point"]: ap["total"]
                for ap in access_points
            }
        }

    @handle_errors
    async def cleanup_old_logs(self, days: int = 90) -> int:
        """
        Remove old access logs
        
        Args:
            days: Remove logs older than this many days
            
        Returns:
            Number of logs removed
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted = await self.db.access_log.delete_many(
            filters={"access_time__lt": cutoff_date}
        )
        
        logger.info(f"Cleaned up {deleted} old access logs")
        return deleted 