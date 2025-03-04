from fastapi import APIRouter, Depends, HTTPException, WebSocket
from typing import List, Dict
from core.security.api_security import SecurityManager
from core.camera.manager import CameraManager
from core.auth.permissions import PermissionManager
from core.error_handling import handle_exceptions

router = APIRouter()
security = SecurityManager()
camera_manager = CameraManager()
permission_manager = PermissionManager()

@router.get("/cameras/live")
@handle_exceptions(logger=mobile_logger.error)
async def get_live_feeds(
    current_user = Depends(security.verify_token)
):
    if not await permission_manager.check_permission(
        current_user['id'], 
        'view_cameras'
    ):
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view cameras"
        )
    
    streams = await camera_manager.get_active_streams()
    return {
        'streams': [
            {
                'id': stream.id,
                'name': stream.name,
                'status': stream.status,
                'thumbnail': await stream.get_thumbnail()
            }
            for stream in streams
        ]
    }

@router.websocket("/ws/camera/{camera_id}")
async def camera_websocket(
    websocket: WebSocket,
    camera_id: int,
    token: str
):
    try:
        user = await security.verify_token(token)
        if not await permission_manager.check_permission(
            user['id'],
            'view_cameras'
        ):
            await websocket.close(code=4003)
            return
            
        await websocket.accept()
        await camera_manager.stream_to_client(camera_id, websocket)
    except Exception as e:
        mobile_logger.error(f"WebSocket error: {e}")
        await websocket.close(code=4000)

@router.post("/permissions/{user_id}")
async def update_permissions(
    user_id: int,
    permissions: Dict[str, bool],
    current_user = Depends(security.verify_token)
):
    if not await permission_manager.check_permission(
        current_user['id'],
        'manage_permissions'
    ):
        raise HTTPException(
            status_code=403,
            detail="Not authorized to manage permissions"
        )
        
    await permission_manager.update_user_permissions(user_id, permissions)
    return {"status": "success"} 
