from enum import Enum
from typing import Set, Dict
from dataclasses import dataclass

class Permission(Enum):
    VIEW_CAMERAS = "view_cameras"
    CONTROL_CAMERAS = "control_cameras"
    VIEW_ALERTS = "view_alerts"
    MANAGE_ALERTS = "manage_alerts"
    MANAGE_USERS = "manage_users"
    SYSTEM_CONFIG = "system_config"
    VIEW_LOGS = "view_logs"
    EXPORT_DATA = "export_data"

@dataclass
class Role:
    name: str
    permissions: Set[Permission]

class PermissionManager:
    def __init__(self):
        self.roles: Dict[str, Role] = {
            "admin": Role("Administrator", set(Permission)),
            "supervisor": Role("Supervisor", {
                Permission.VIEW_CAMERAS,
                Permission.CONTROL_CAMERAS,
                Permission.VIEW_ALERTS,
                Permission.MANAGE_ALERTS,
                Permission.VIEW_LOGS
            }),
            "operator": Role("Operator", {
                Permission.VIEW_CAMERAS,
                Permission.VIEW_ALERTS,
                Permission.VIEW_LOGS
            })
        }

    async def check_permission(self, user_id: int, permission: Permission) -> bool:
        user_role = await self.get_user_role(user_id)
        return permission in self.roles[user_role].permissions

    @handle_exceptions(logger=auth_logger.error)
    async def get_user_role(self, user_id: int) -> str:
        # Get role from database
        async with self.db_pool.get_connection() as conn:
            result = await conn.fetchrow(
                "SELECT role FROM users WHERE id = $1",
                user_id
            )
            return result['role'] if result else "operator" 
