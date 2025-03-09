import { useContext, useEffect } from 'react';
import { AuthContext } from '@/app/providers/AuthProvider';
import type { User, Permission } from '@/lib/auth/types';
import { useRouter } from 'next/navigation';

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export function useUser() {
  const { user } = useAuth();
  return user;
}

export function useIsAuthenticated() {
  const { isAuthenticated } = useAuth();
  return isAuthenticated;
}

export function useIsLoading() {
  const { isLoading } = useAuth();
  return isLoading;
}

export function useAuthError() {
  const { error } = useAuth();
  return error;
}

export function useHasPermission(permission: string) {
  const { user } = useAuth();
  if (!user) return false;
  return user.permissions.some(p => p.value === permission);
}

export function useHasRole(role: string) {
  const { user } = useAuth();
  if (!user) return false;
  return user.role === role;
}

export function useHasZoneAccess(zoneId: string) {
  const { user } = useAuth();
  if (!user) return false;
  return user.zones.some(z => z.id === zoneId);
}

export function useRequireAuth() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  return { isAuthenticated, isLoading };
}

export function useRequirePermission(permission: string) {
  const hasPermission = useHasPermission(permission);
  const { isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !hasPermission) {
      router.push('/unauthorized');
    }
  }, [hasPermission, isLoading, router]);

  return { hasPermission, isLoading };
}

export function useRequireRole(role: string) {
  const hasRole = useHasRole(role);
  const { isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !hasRole) {
      router.push('/unauthorized');
    }
  }, [hasRole, isLoading, router]);

  return { hasRole, isLoading };
}

export function useRequireZoneAccess(zoneId: string) {
  const hasAccess = useHasZoneAccess(zoneId);
  const { isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !hasAccess) {
      router.push('/unauthorized');
    }
  }, [hasAccess, isLoading, router]);

  return { hasAccess, isLoading };
} 