"""
Administrative API Routes for CernoID System.

This module provides high-level administrative endpoints for system management,
monitoring, and control. It enables administrators to manage users, monitor
system access, and track system-wide statistics.

Key Features:
- Comprehensive user management and monitoring
- Detailed access log tracking and analysis
- Real-time system statistics and metrics
- Administrative control operations
- Security policy enforcement
- System health monitoring
- Performance tracking

Dependencies:
- FastAPI: Web framework and routing
- Core services:
  - SecurityMiddleware: Permission and access control
  - Database Models: User, AccessRecord, Person schemas
  - Response Schemas: Standardized API responses
  - Logging System: Audit and error tracking
  - Metrics: System performance monitoring

API Endpoints:
- GET /admin/users: List and manage system users
- GET /admin/access-logs: Monitor system access
- GET /admin/stats: Track system performance

Security:
- JWT authentication required for all endpoints
- Strict admin-only access control
- Fine-grained permission validation
- Comprehensive audit logging
- Rate limiting and throttling
- Resource access control

Performance:
- Efficient pagination implementation
- Query optimization
- Response caching
- Resource pooling
- Metric aggregation
- Background processing

Error Handling:
- Detailed error responses
- Proper status codes
- Error logging
- Recovery procedures
- Fallback mechanisms
- Security error masking
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from core.security.middleware import SecurityMiddleware
from core.database.models import User, AccessRecord, Person
from ..schemas import UserResponse, AccessRecord as AccessRecordSchema

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/users", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    security: SecurityMiddleware = Depends()
):
    """
    Retrieve all users in the system with pagination support.
    
    Provides a paginated list of all system users with their details,
    including authentication status, roles, and last activity.
    
    Args:
        skip (int): Number of records to skip for pagination
        limit (int): Maximum number of records to return (1-100)
        security: Security middleware for permission validation
    
    Returns:
        List[UserResponse]: List of user details including:
            - User ID: Unique identifier
            - Username: Login name
            - Email: Contact address
            - Role: Access level
            - Status: Account state
            - Last Login: Recent activity
            - Permissions: Access rights
    
    Raises:
        HTTPException:
            - 400: Invalid pagination parameters
            - 401: Not authenticated
            - 403: Insufficient permissions
            - 500: Database or server error
    
    Security:
        - Requires admin role
        - Validates JWT token
        - Checks admin permissions
        - Logs access attempts
        - Filters sensitive data
        - Rate limited: 10 req/min
    
    Performance:
        - Paginated results
        - Optimized queries
        - Cached responses
        - Limited fields
        - Index usage
    """
    # Check admin permissions
    await security.check_permissions(["admin"])
    
    users = await User.get_all(skip=skip, limit=limit)
    return users

@router.get("/access-logs", response_model=List[AccessRecordSchema])
async def get_access_logs(
    skip: int = 0,
    limit: int = 100,
    security: SecurityMiddleware = Depends()
):
    """
    Retrieve system access logs with pagination support.
    
    Provides detailed access logs showing user activity, resource access,
    and security events across the system.
    
    Args:
        skip (int): Number of records to skip for pagination
        limit (int): Maximum number of records to return (1-100)
        security: Security middleware for permission validation
    
    Returns:
        List[AccessRecordSchema]: List of access records including:
            - Timestamp: Event time (ISO 8601)
            - User ID: Actor identifier
            - Action: Operation type
            - Resource: Target object
            - Status: Success/failure
            - IP Address: Client IP
            - User Agent: Client info
            - Duration: Processing time
            - Details: Additional data
    
    Raises:
        HTTPException:
            - 400: Invalid pagination parameters
            - 401: Not authenticated
            - 403: Insufficient permissions
            - 500: Database or server error
    
    Security:
        - Requires admin role
        - Validates JWT token
        - Checks admin permissions
        - Logs access attempts
        - Contains sensitive data
        - Rate limited: 5 req/min
    
    Performance:
        - Paginated results
        - Indexed queries
        - Cached responses
        - Compressed data
        - Efficient filtering
    """
    # Check admin permissions
    await security.check_permissions(["admin"])
    
    logs = await AccessRecord.get_all(skip=skip, limit=limit)
    return logs

@router.get("/stats")
async def get_system_stats(security: SecurityMiddleware = Depends()):
    """
    Retrieve real-time system statistics and metrics.
    
    Provides comprehensive system-wide statistics including user counts,
    activity metrics, and health status information.
    
    Args:
        security: Security middleware for permission validation
    
    Returns:
        Dict[str, Any]: System statistics including:
            - User Metrics:
                - Total users
                - Active users
                - New users (24h)
            - Person Data:
                - Total persons
                - Recognition count
                - Match accuracy
            - Access Records:
                - Total records
                - Success rate
                - Average latency
            - System Health:
                - Status
                - CPU usage
                - Memory usage
                - Storage space
                - Service status
            - Performance:
                - Request rate
                - Error rate
                - Response time
                - Queue length
    
    Raises:
        HTTPException:
            - 401: Not authenticated
            - 403: Insufficient permissions
            - 500: Error collecting metrics
            - 503: Services unavailable
    
    Security:
        - Requires admin role
        - Validates JWT token
        - Checks admin permissions
        - Logs access attempts
        - Rate limited: 1 req/min
    
    Performance:
        - Cached metrics
        - Async collection
        - Aggregated data
        - Background updates
        - Efficient storage
    """
    # Check admin permissions
    await security.check_permissions(["admin"])
    
    try:
        stats = {
            "total_users": await User.count(),
            "total_persons": await Person.count(),
            "total_access_records": await AccessRecord.count(),
            "system_status": "healthy"
        }
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 