from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from core.security.middleware import SecurityMiddleware
from core.database.models import User, AccessRecord
from ..schemas import UserResponse, AccessRecord as AccessRecordSchema

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/users", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    security: SecurityMiddleware = Depends()
):
    """Get all users"""
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
    """Get access logs"""
    # Check admin permissions
    await security.check_permissions(["admin"])
    
    logs = await AccessRecord.get_all(skip=skip, limit=limit)
    return logs

@router.get("/stats")
async def get_system_stats(security: SecurityMiddleware = Depends()):
    """Get system statistics"""
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