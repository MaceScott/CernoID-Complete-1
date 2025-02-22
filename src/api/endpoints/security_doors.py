from fastapi import APIRouter, Depends, HTTPException
from typing import List
from core.access.access_control import AccessController
from core.auth.authenticator import AuthManager
from core.error_handling import handle_exceptions

router = APIRouter()
access_controller = AccessController()
auth_manager = AuthManager()

@router.post("/doors/{door_id}/open")
@handle_exceptions(logger=door_logger.error)
async def open_door(
    door_id: str,
    zone_id: int,
    current_user = Depends(auth_manager.get_current_user)
):
    if not await access_controller.check_access(current_user.id, zone_id):
        raise HTTPException(
            status_code=403,
            detail="Access denied to this zone"
        )
    
    try:
        await DoorController.open_door(door_id)
        return {"status": "success", "message": "Door opened"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to open door: {str(e)}"
        )

@router.get("/zones/{zone_id}/status")
async def get_zone_status(
    zone_id: int,
    current_user = Depends(auth_manager.get_current_user)
):
    zone = access_controller.zones.get(zone_id)
    if not zone:
        raise HTTPException(
            status_code=404,
            detail="Zone not found"
        )
    
    door_statuses = await DoorController.get_zone_door_statuses(
        zone.door_controllers
    )
    return {
        "zone_id": zone_id,
        "name": zone.name,
        "door_statuses": door_statuses
    } 
