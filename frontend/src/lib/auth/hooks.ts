import { useContext } from 'react';
import { AuthContext } from '@/app/providers/AuthProvider';
import type { User, AuthState } from './types';
import { hasPermission, hasRole, hasZoneAccess } from './utils';

interface AuthContextType extends AuthState {
  login: (credentials: { email: string; password: string; remember?: boolean }) => Promise<void>;
  register: (data: { email: string; password: string; name: string; confirmPassword: string }) => Promise<void>;
  logout: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
  updatePassword: (token: string, password: string, confirmPassword: string) => Promise<void>;
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export function useUser(): User | null {
  const { user } = useAuth();
  return user;
}

export function useIsAuthenticated(): boolean {
  const { isAuthenticated } = useAuth();
  return isAuthenticated;
}

export function useIsLoading(): boolean {
  const { isLoading } = useAuth();
  return isLoading;
}

export function useAuthError(): string | null {
  const { error } = useAuth();
  return error;
}

export function useHasPermission(permission: string): boolean {
  const { user } = useAuth();
  return hasPermission(user, permission);
}

export function useHasRole(role: string): boolean {
  const { user } = useAuth();
  return hasRole(user, role);
}

export function useHasZoneAccess(zoneId: string): boolean {
  const { user } = useAuth();
  return hasZoneAccess(user, zoneId);
}

export function useRequireAuth() {
  const { isAuthenticated, isLoading } = useAuth();
  
  if (!isLoading && !isAuthenticated) {
    throw new Error('User must be authenticated');
  }
  
  return { isLoading };
}

export function useRequirePermission(permission: string) {
  const { user, isLoading } = useAuth();
  
  if (!isLoading && !hasPermission(user, permission)) {
    throw new Error(`User must have permission: ${permission}`);
  }
  
  return { isLoading };
}

export function useRequireRole(role: string) {
  const { user, isLoading } = useAuth();
  
  if (!isLoading && !hasRole(user, role)) {
    throw new Error(`User must have role: ${role}`);
  }
  
  return { isLoading };
}

export function useRequireZoneAccess(zoneId: string) {
  const { user, isLoading } = useAuth();
  
  if (!isLoading && !hasZoneAccess(user, zoneId)) {
    throw new Error(`User must have access to zone: ${zoneId}`);
  }
  
  return { isLoading };
} 