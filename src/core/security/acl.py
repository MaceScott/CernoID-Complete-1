"""
Access Control List (ACL) system with role-based permissions.
"""
from typing import Dict, List, Optional, Set
from enum import Enum
import json
from pathlib import Path
from datetime import datetime
import yaml

from ..utils.config import get_settings
from ..utils.logging import get_logger
from ..database.service import DatabaseService

class Permission(str, Enum):
    """Permission types."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"

class Resource(str, Enum):
    """Resource types."""
    CAMERA = "camera"
    USER = "user"
    RECOGNITION = "recognition"
    SYSTEM = "system"
    AUDIT = "audit"

class ACLSystem:
    """
    Advanced Access Control List system
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.db = DatabaseService()
        
        # Load ACL configuration
        self.acl_config = self._load_acl_config()
        
        # Initialize cache
        self.permission_cache: Dict[str, Dict[str, Set[str]]] = {}
        
    def _load_acl_config(self) -> Dict:
        """Load ACL configuration from file."""
        config_path = Path(self.settings.config_dir) / "acl.yml"
        
        try:
            with open(config_path) as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Failed to load ACL config: {str(e)}")
            return {}
            
    async def check_permission(self,
                             user_id: int,
                             resource: Resource,
                             permission: Permission) -> bool:
        """Check if user has permission for resource."""
        try:
            # Check cache first
            cache_key = f"{user_id}:{resource}"
            if cache_key in self.permission_cache:
                permissions = self.permission_cache[cache_key]
                if permission in permissions:
                    return True
                    
            # Get user roles
            user = await self.db.get_user(user_id)
            if not user:
                return False
                
            roles = user.roles
            
            # Check permissions for each role
            for role in roles:
                role_permissions = self.acl_config.get(role, {})
                resource_permissions = role_permissions.get(resource, [])
                
                if permission in resource_permissions:
                    # Update cache
                    if cache_key not in self.permission_cache:
                        self.permission_cache[cache_key] = set()
                    self.permission_cache[cache_key].add(permission)
                    return True
                    
            return False
            
        except Exception as e:
            self.logger.error(f"Permission check failed: {str(e)}")
            return False
            
    async def grant_permission(self,
                             role: str,
                             resource: Resource,
                             permission: Permission) -> bool:
        """Grant permission to role."""
        try:
            if role not in self.acl_config:
                self.acl_config[role] = {}
                
            if resource not in self.acl_config[role]:
                self.acl_config[role][resource] = []
                
            if permission not in self.acl_config[role][resource]:
                self.acl_config[role][resource].append(permission)
                
            # Save updated config
            await self._save_acl_config()
            
            # Clear cache
            self.permission_cache.clear()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to grant permission: {str(e)}")
            return False
            
    async def revoke_permission(self,
                              role: str,
                              resource: Resource,
                              permission: Permission) -> bool:
        """Revoke permission from role."""
        try:
            if (role in self.acl_config and
                resource in self.acl_config[role] and
                permission in self.acl_config[role][resource]):
                
                self.acl_config[role][resource].remove(permission)
                
                # Save updated config
                await self._save_acl_config()
                
                # Clear cache
                self.permission_cache.clear()
                
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to revoke permission: {str(e)}")
            return False
            
    async def _save_acl_config(self):
        """Save ACL configuration to file."""
        config_path = Path(self.settings.config_dir) / "acl.yml"
        
        try:
            with open(config_path, 'w') as f:
                yaml.safe_dump(self.acl_config, f)
        except Exception as e:
            self.logger.error(f"Failed to save ACL config: {str(e)}")
            raise
            
    def get_role_permissions(self,
                           role: str) -> Dict[str, List[str]]:
        """Get all permissions for a role."""
        return self.acl_config.get(role, {})
        
    def get_resource_roles(self,
                         resource: Resource) -> List[str]:
        """Get all roles with access to a resource."""
        roles = []
        for role, permissions in self.acl_config.items():
            if resource in permissions:
                roles.append(role)
        return roles

# Global ACL system instance
acl_system = ACLSystem() 