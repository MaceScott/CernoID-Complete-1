from typing import Dict, List
from datetime import datetime
from core.auth.permissions import PermissionManager
from core.error_handling import handle_exceptions
from core.mobile.notification_service import MobileNotificationService, MobileNotification

class MobilePermissionController:
    def __init__(self):
        self.permission_manager = PermissionManager()
        self.notification_service = MobileNotificationService()

    @handle_exceptions(logger=permission_logger.error)
    async def update_user_permissions(
        self,
        user_id: int,
        permissions: Dict[str, bool],
        admin_id: int
    ):
        # Verify admin permissions
        if not await self.permission_manager.check_permission(
            admin_id,
            'manage_permissions'
        ):
            raise PermissionError("Not authorized to manage permissions")

        # Update permissions
        await self.permission_manager.set_user_permissions(
            user_id,
            permissions
        )

        # Notify relevant users
        await self._notify_permission_change(user_id, permissions)

    async def _notify_permission_change(
        self,
        user_id: int,
        permissions: Dict[str, bool]
    ):
        user_tokens = await self._get_user_device_tokens(user_id)
        if user_tokens:
            notification = MobileNotification(
                title="Permissions Updated",
                body="Your access permissions have been updated",
                data={
                    'type': 'permission_update',
                    'permissions': permissions,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            await self.notification_service.send_notification(
                notification,
                user_tokens
            )

    async def _get_user_device_tokens(self, user_id: int) -> List[str]:
        async with self.db_pool.acquire() as conn:
            tokens = await conn.fetch(
                "SELECT device_token FROM user_devices WHERE user_id = $1",
                user_id
            )
            return [token['device_token'] for token in tokens]
