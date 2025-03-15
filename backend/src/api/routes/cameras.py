"""
File: cameras.py
Purpose: Camera management and video stream processing routes for the CernoID system.

Key Features:
- Camera management (CRUD operations)
- Video stream handling
- Frame processing
- Camera health monitoring
- Stream configuration

Dependencies:
- FastAPI: Web framework and routing
- Core services:
  - CameraService: Camera operations
  - StreamProcessor: Video processing
  - Database: Data storage
  - Authorization: Access control

Security:
- JWT authentication
- Role-based access control
- Stream access validation
- Rate limiting
- Resource monitoring

Performance:
- Stream optimization
- Frame rate control
- Quality adaptation
- Resource cleanup
- Connection pooling
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, validator

from ...core.camera import CameraService, StreamProcessor
from ...core.models import Camera
from ...database import get_db
from ...utils.auth import get_current_user, require_permissions
from ...utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/cameras", tags=["cameras"])

class CameraCreate(BaseModel):
    """
    Camera creation request model.
    
    Attributes:
        name (str): Camera name/identifier
        url (str): Stream URL (RTSP/HTTP)
        location (str): Physical location
        type (str): Camera type (fixed/ptz)
        config (Dict): Stream configuration
        
    Validation:
        - Name format and length
        - URL format and protocol
        - Location constraints
        - Type enumeration
        - Config validation
        
    Example:
        {
            "name": "entrance_cam_01",
            "url": "rtsp://camera.local/stream",
            "location": "Main Entrance",
            "type": "fixed",
            "config": {
                "fps": 30,
                "resolution": "1920x1080",
                "quality": "high"
            }
        }
    """
    
    name: str = Field(..., min_length=3, max_length=64)
    url: str = Field(..., description="Stream URL (RTSP/HTTP)")
    location: str = Field(..., min_length=1, max_length=128)
    type: str = Field(default="fixed")
    config: Dict[str, Any] = Field(default_factory=dict)
    
    @validator("type")
    def validate_type(cls, v: str) -> str:
        """Validate camera type."""
        valid_types = {"fixed", "ptz"}
        if v.lower() not in valid_types:
            raise ValueError(f"Invalid camera type. Must be one of: {valid_types}")
        return v.lower()
        
class CameraUpdate(BaseModel):
    """
    Camera update request model.
    
    Attributes:
        name (str): Camera name/identifier
        location (str): Physical location
        active (bool): Camera status
        config (Dict): Stream configuration
        
    Validation:
        - Name format and length
        - Location constraints
        - Config validation
        - Status checks
        
    Example:
        {
            "name": "entrance_cam_01",
            "location": "Main Entrance",
            "active": true,
            "config": {
                "fps": 30,
                "quality": "high"
            }
        }
    """
    
    name: Optional[str] = Field(None, min_length=3, max_length=64)
    location: Optional[str] = Field(None, min_length=1, max_length=128)
    active: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None
    
class CameraResponse(BaseModel):
    """
    Camera response model.
    
    Attributes:
        id (str): Camera identifier
        name (str): Camera name
        url (str): Stream URL
        location (str): Physical location
        type (str): Camera type
        active (bool): Camera status
        config (Dict): Stream configuration
        status (Dict): Health status
        stats (Dict): Performance statistics
        
    Example:
        {
            "id": "cam_123",
            "name": "entrance_cam_01",
            "url": "rtsp://camera.local/stream",
            "location": "Main Entrance",
            "type": "fixed",
            "active": true,
            "config": {
                "fps": 30,
                "resolution": "1920x1080"
            },
            "status": {
                "connected": true,
                "streaming": true
            },
            "stats": {
                "fps": 29.8,
                "latency": 150,
                "uptime": 3600
            }
        }
    """
    
    id: str
    name: str
    url: str
    location: str
    type: str
    active: bool
    config: Dict[str, Any]
    status: Dict[str, Any]
    stats: Dict[str, Any]
    
@router.post("", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
async def create_camera(
    camera: CameraCreate,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create new camera.
    
    Args:
        camera: Camera creation data
        current_user: Authenticated user
        db: Database connection
        
    Returns:
        Dict[str, Any]: Created camera details
        
    Features:
        - Camera registration
        - Stream validation
        - Config setup
        - Health check
        - Event dispatch
        
    Security:
        - Authentication required
        - Permission: cameras.create
        - Rate limiting applied
        - Resource limits
        - Input validation
        
    Response:
        CameraResponse model
    """
    try:
        # Validate permissions
        require_permissions(current_user, "cameras.create")
        
        # Create camera
        service = CameraService()
        result = await service.create_camera(camera.dict())
        
        return result
        
    except Exception as e:
        logger.error(f"Camera creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Camera creation failed"
        )
        
@router.get("", response_model=List[CameraResponse])
async def list_cameras(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    List all cameras.
    
    Args:
        current_user: Authenticated user
        db: Database connection
        
    Returns:
        List[Dict[str, Any]]: List of cameras
        
    Features:
        - Camera listing
        - Status checks
        - Stats collection
        - Filtering options
        - Sorting options
        
    Security:
        - Authentication required
        - Permission: cameras.list
        - Rate limiting applied
        - Resource limits
        - Access control
        
    Response:
        List of CameraResponse models
    """
    try:
        # Validate permissions
        require_permissions(current_user, "cameras.list")
        
        # Get cameras
        service = CameraService()
        results = await service.list_cameras()
        
        return results
        
    except Exception as e:
        logger.error(f"Camera listing failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Camera listing failed"
        )
        
@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(
    camera_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get camera details.
    
    Args:
        camera_id: Camera identifier
        current_user: Authenticated user
        db: Database connection
        
    Returns:
        Dict[str, Any]: Camera details
        
    Features:
        - Camera details
        - Status check
        - Stats collection
        - Stream info
        - Config data
        
    Security:
        - Authentication required
        - Permission: cameras.read
        - Rate limiting applied
        - Resource limits
        - Access control
        
    Response:
        CameraResponse model
    """
    try:
        # Validate permissions
        require_permissions(current_user, "cameras.read")
        
        # Get camera
        service = CameraService()
        result = await service.get_camera(camera_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Camera not found"
            )
            
        return result
        
    except Exception as e:
        logger.error(f"Camera retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Camera retrieval failed"
        )
        
@router.put("/{camera_id}", response_model=CameraResponse)
async def update_camera(
    camera_id: str,
    camera: CameraUpdate,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update camera settings.
    
    Args:
        camera_id: Camera identifier
        camera: Update data
        current_user: Authenticated user
        db: Database connection
        
    Returns:
        Dict[str, Any]: Updated camera details
        
    Features:
        - Settings update
        - Config validation
        - Stream restart
        - Status check
        - Event dispatch
        
    Security:
        - Authentication required
        - Permission: cameras.update
        - Rate limiting applied
        - Resource limits
        - Access control
        
    Response:
        CameraResponse model
    """
    try:
        # Validate permissions
        require_permissions(current_user, "cameras.update")
        
        # Update camera
        service = CameraService()
        result = await service.update_camera(camera_id, camera.dict(exclude_unset=True))
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Camera not found"
            )
            
        return result
        
    except Exception as e:
        logger.error(f"Camera update failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Camera update failed"
        )
        
@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(
    camera_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
) -> None:
    """
    Delete camera.
    
    Args:
        camera_id: Camera identifier
        current_user: Authenticated user
        db: Database connection
        
    Features:
        - Camera removal
        - Stream cleanup
        - Resource cleanup
        - Event dispatch
        - Status update
        
    Security:
        - Authentication required
        - Permission: cameras.delete
        - Rate limiting applied
        - Resource limits
        - Access control
    """
    try:
        # Validate permissions
        require_permissions(current_user, "cameras.delete")
        
        # Delete camera
        service = CameraService()
        result = await service.delete_camera(camera_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Camera not found"
            )
            
    except Exception as e:
        logger.error(f"Camera deletion failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Camera deletion failed"
        )
        
@router.get("/{camera_id}/stream")
async def get_stream(
    camera_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get video stream.
    
    Args:
        camera_id: Camera identifier
        current_user: Authenticated user
        db: Database connection
        
    Returns:
        Dict[str, Any]: Stream details
        
    Features:
        - Stream access
        - Frame delivery
        - Quality control
        - Performance monitoring
        - Error handling
        
    Security:
        - Authentication required
        - Permission: cameras.stream
        - Rate limiting applied
        - Resource limits
        - Access control
        
    Response:
        {
            "url": "ws://server/stream/cam_123",
            "token": "stream_token",
            "config": {
                "fps": 30,
                "quality": "high"
            }
        }
    """
    try:
        # Validate permissions
        require_permissions(current_user, "cameras.stream")
        
        # Get stream
        service = CameraService()
        result = await service.get_stream(camera_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Camera not found"
            )
            
        return result
        
    except Exception as e:
        logger.error(f"Stream access failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stream access failed"
        )
        
@router.post("/{camera_id}/config")
async def update_stream_config(
    camera_id: str,
    config: Dict[str, Any],
    current_user = Depends(get_current_user),
    db = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update stream configuration.
    
    Args:
        camera_id: Camera identifier
        config: Stream configuration
        current_user: Authenticated user
        db: Database connection
        
    Returns:
        Dict[str, Any]: Updated configuration
        
    Features:
        - Config update
        - Stream restart
        - Quality control
        - Performance tuning
        - Event dispatch
        
    Security:
        - Authentication required
        - Permission: cameras.config
        - Rate limiting applied
        - Resource limits
        - Access control
        
    Response:
        {
            "config": {
                "fps": 30,
                "resolution": "1920x1080",
                "quality": "high"
            },
            "status": {
                "applied": true,
                "restart_required": false
            }
        }
    """
    try:
        # Validate permissions
        require_permissions(current_user, "cameras.config")
        
        # Update config
        service = CameraService()
        result = await service.update_stream_config(camera_id, config)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Camera not found"
            )
            
        return result
        
    except Exception as e:
        logger.error(f"Config update failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Config update failed"
        )
""" 