import { type User } from 'next-auth';

export function hasPermission(user: User | null, permission: string): boolean {
  if (!user) return false;
  // Check if user has admin access
  if (user.isAdmin) return true;
  // Check if user has the required permission
  return user.accessLevel >= 3; // Admin level
}

export function hasRole(user: User | null, role: string): boolean {
  if (!user) return false;
  return user.role.toLowerCase() === role.toLowerCase();
}

export function hasZoneAccess(user: User | null, zoneId: string): boolean {
  if (!user) return false;
  // Admin has access to all zones
  if (user.isAdmin) return true;
  // Check if user has access to the zone
  return user.allowedZones.includes(zoneId);
}

export function getHighestSecurityLevel(user: User | null): number {
  if (!user) return 0;
  return user.accessLevel;
}

export function formatPermission(type: string, value: string): string {
  return `${type}:${value}`;
}

export function parsePermission(formatted: string): { type: string; value: string } {
  const [type = '', value = ''] = formatted.split(':');
  return { type, value };
}

export function getZoneHierarchy(user: User | null, zoneId: string): string[] {
  if (!user) return [];
  const zones = user.allowedZones;
  const hierarchy: string[] = [];
  
  let currentId: string | undefined = zoneId;
  while (currentId && zones.includes(currentId)) {
    hierarchy.unshift(currentId);
    currentId = parseZoneId(currentId).parentId;
  }
  
  return hierarchy;
}

function parseZoneId(zoneId: string): { id: string; parentId?: string } {
  const [id = '', parentId = ''] = zoneId.split('|');
  return { id, parentId: parentId || undefined };
} 