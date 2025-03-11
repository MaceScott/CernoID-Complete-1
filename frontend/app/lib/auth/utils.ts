import { type User } from './types';

export function hasPermission(user: User | null, permission: string): boolean {
  if (!user) return false;
  return user.permissions.includes(permission);
}

export function hasRole(user: User | null, role: string): boolean {
  if (!user) return false;
  return user.role === role;
}

export function hasZoneAccess(user: User | null, zoneId: string): boolean {
  if (!user) return false;
  return user.zones.includes(zoneId);
}

export function getHighestSecurityLevel(user: User | null): number {
  if (!user) return 0;
  return Math.max(...user.zones.map(z => parseInt(z.split(':')[1] || '0', 10)), 0);
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
  const zones = user.zones;
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