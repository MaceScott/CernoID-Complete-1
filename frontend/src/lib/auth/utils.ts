import { type User, type Permission } from './types';

export function hasPermission(user: User | null, permission: string): boolean {
  if (!user) return false;
  return user.permissions.some(p => p.value === permission);
}

export function hasRole(user: User | null, role: string): boolean {
  if (!user) return false;
  return user.role === role;
}

export function hasZoneAccess(user: User | null, zoneId: string): boolean {
  if (!user) return false;
  return user.zones.some(z => z.id === zoneId);
}

export function getHighestSecurityLevel(user: User | null): number {
  if (!user) return 0;
  const levels = user.zones.map(z => z.level);
  return Math.max(...levels, 0);
}

export function formatPermission(permission: Permission): string {
  return `${permission.type}:${permission.value}`;
}

export function parsePermission(formatted: string): { type: string; value: string } {
  const [type = '', value = ''] = formatted.split(':');
  return { type, value };
}

export function getZoneHierarchy(user: User | null, zoneId: string): string[] {
  if (!user) return [];
  const zones = user.zones;
  const hierarchy: string[] = [];
  
  let currentZone = zones.find(z => z.id === zoneId);
  while (currentZone?.id) {
    hierarchy.unshift(currentZone.id);
    const parentId = currentZone.parent_id;
    currentZone = parentId ? zones.find(z => z.id === parentId) : undefined;
  }
  
  return hierarchy;
} 