'use client';

import { useContext } from 'react';
import { AuthContext } from '../providers/AuthProvider';
import { AuthContextType } from '@/lib/auth/types';
import { useRouter } from 'next/navigation';

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export function useRequireAuth() {
  const { user } = useAuth();
  const router = useRouter();

  if (!user) {
    router.push('/login');
  }

  return user;
}

export function useHasRole(role: string) {
  const { user } = useAuth();
  if (!user) return false;
  return user.role === role;
}

export function useHasPermission(permission: string) {
  const { user } = useAuth();
  if (!user) return false;
  return user.permissions.includes(permission);
}

export function useHasZoneAccess(zoneId: string) {
  const { user } = useAuth();
  if (!user) return false;
  return user.zones.includes(zoneId);
}

export function useRequireRole(role: string) {
  const { user } = useAuth();
  const router = useRouter();

  if (!user || user.role !== role) {
    router.push('/unauthorized');
  }

  return user;
}

export function useRequirePermission(permission: string) {
  const { user } = useAuth();
  const router = useRouter();

  if (!user || !user.permissions.includes(permission)) {
    router.push('/unauthorized');
  }

  return user;
}

export function useRequireZoneAccess(zoneId: string) {
  const { user } = useAuth();
  const router = useRouter();

  if (!user || !user.zones.includes(zoneId)) {
    router.push('/unauthorized');
  }

  return user;
} 