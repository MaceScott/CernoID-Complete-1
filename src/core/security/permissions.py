from typing import Dict, Set, Optional, Any, Callable, List
from functools import wraps
from fastapi import HTTPException, Request
from ..base import BaseComponent
from ..utils.errors import handle_errors

class PermissionManager(BaseComponent):
    """Permission and role management system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._roles: Dict[str, Set[str]] = {}
        self._permissions: Dict[str, Set[str]] = {}
        self._role_hierarchy: Dict[str, Set[str]] = {}

    async def initialize(self) -> None:
        """Initialize permission manager"""
        # Load roles and permissions
        await self._load_roles()
        await self._load_permissions()

    async def cleanup(self) -> None:
        """Cleanup permission resources"""
        self._roles.clear()
        self._permissions.clear()
        self._role_hierarchy.clear()

    def requires_permission(self, permission: str):
        """Permission requirement decorator"""
        
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Get request object
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                        
                if not request:
                    raise RuntimeError("No request object found")
                    
                # Check permission
                user = request.state.user
                if not user:
                    raise HTTPException(
                        status_code=401,
                        detail="Authentication required"
                    )
                    
                if not await self.has_permission(
                    user['id'],
                    permission
                ):
                    raise HTTPException(
                        status_code=403,
                        detail="Permission denied"
                    )
                    
                return await func(*args, **kwargs)
                
            return wrapper
            
        return decorator

    def requires_role(self, role: str):
        """Role requirement decorator"""
        
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Get request object
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                        
                if not request:
                    raise RuntimeError("No request object found")
                    
                # Check role
                user = request.state.user
                if not user:
                    raise HTTPException(
                        status_code=401,
                        detail="Authentication required"
                    )
                    
                if not await self.has_role(
                    user['id'],
                    role
                ):
                    raise HTTPException(
                        status_code=403,
                        detail="Role required"
                    )
                    
                return await func(*args, **kwargs)
                
            return wrapper
            
        return decorator

    @handle_errors(logger=None)
    async def has_permission(self,
                             user_id: str,
                             permission: str) -> bool:
        try:
            db = self.app.get_component('database')
            roles = await db.fetch_all(
                "SELECT role FROM user_roles WHERE user_id = $1",
                user_id
            )

            user_roles = {r['role'] for r in roles}

            for role in user_roles:
                if permission in self._roles.get(role, set()):
                    self.logger.info(f"Permission '{permission}' found for user '{user_id}' in role '{role}'")
                    return True

                inherited = self._role_hierarchy.get(role, set())
                for inherited_role in inherited:
                    if permission in self._roles.get(inherited_role, set()):
                        self.logger.info(f"Permission '{permission}' inherited for user '{user_id}' from role '{inherited_role}'")
                        return True

            self.logger.warning(f"Permission '{permission}' not found for user '{user_id}'")
            return False

        except Exception as e:
            self.logger.error(f"Permission check failed for user '{user_id}': {str(e)}")
            raise

    @handle_errors(logger=None)
    async def has_role(self,
                       user_id: str,
                       role: str) -> bool:
        try:
            db = self.app.get_component('database')
            result = await db.fetch_one(
                "SELECT 1 FROM user_roles WHERE user_id = $1 AND role = $2",
                user_id,
                role
            )
            if result:
                self.logger.info(f"User '{user_id}' has role '{role}'")
            else:
                self.logger.warning(f"User '{user_id}' does not have role '{role}'")
            return bool(result)
        except Exception as e:
            self.logger.error(f"Role check failed for user '{user_id}': {str(e)}")
            raise

    async def grant_permission(self,
                             role: str,
                             permission: str) -> None:
        """Grant permission to role"""
        if role not in self._roles:
            self._roles[role] = set()
            
        self._roles[role].add(permission)
        await self._save_roles()

    async def revoke_permission(self,
                              role: str,
                              permission: str) -> None:
        """Revoke permission from role"""
        if role in self._roles:
            self._roles[role].discard(permission)
            await self._save_roles()

    async def add_role_inheritance(self,
                                 role: str,
                                 inherits: str) -> None:
        """Add role inheritance"""
        if role not in self._role_hierarchy:
            self._role_hierarchy[role] = set()
            
        self._role_hierarchy[role].add(inherits)

    async def get_user_permissions(self,
                                 user_id: str) -> Set[str]:
        """Get all user permissions"""
        permissions = set()
        
        # Get user roles
        db = self.app.get_component('database')
        roles = await db.fetch_all(
            "SELECT role FROM user_roles WHERE user_id = $1",
            user_id
        )
        
        # Collect permissions
        for role in roles:
            role_name = role['role']
            permissions.update(self._roles.get(role_name, set()))
            
            # Add inherited permissions
            inherited = self._role_hierarchy.get(role_name, set())
            for inherited_role in inherited:
                permissions.update(
                    self._roles.get(inherited_role, set())
                )
                
        return permissions

    async def _load_roles(self) -> None:
        """Load roles from storage"""
        try:
            db = self.app.get_component('database')
            records = await db.fetch_all("SELECT role, permissions FROM roles")
            for record in records:
                self._roles[record['role']] = set(record['permissions'])
            self.logger.info("Roles loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load roles: {str(e)}")
            raise

    async def _load_permissions(self) -> None:
        """Load permissions from storage"""
        try:
            db = self.app.get_component('database')
            records = await db.fetch_all("SELECT name, description FROM permissions")
            for record in records:
                self._permissions[record['name']] = record['description']
            self.logger.info("Permissions loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load permissions: {str(e)}")
            raise

    async def _save_roles(self) -> None:
        """Save roles to storage"""
        try:
            db = self.app.get_component('database')
            
            # Clear existing roles
            await db.execute("DELETE FROM roles")
            
            # Insert updated roles
            if self._roles:
                await db.execute_many(
                    """
                    INSERT INTO roles (role, permissions)
                    VALUES ($1, $2)
                    """,
                    [
                        (role, list(permissions))
                        for role, permissions in self._roles.items()
                    ]
                )
                
        except Exception as e:
            self.logger.error(f"Failed to save roles: {str(e)}") 