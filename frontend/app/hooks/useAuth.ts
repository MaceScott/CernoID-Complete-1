'use client';

import { useState, useCallback, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api-client';
import type { User, AuthResponse, RegisterData } from '@/lib/auth/types';

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
  lastActivity: number;
}

const SESSION_TIMEOUT = 30 * 60 * 1000; // 30 minutes in milliseconds
const ACTIVITY_CHECK_INTERVAL = 1000; // Check every second
const ACTIVITY_EVENTS = ['mousedown', 'keydown', 'touchstart', 'scroll'];

export function useAuth() {
  const router = useRouter();
  const [state, setState] = useState<AuthState>({
    user: null,
    token: null,
    isLoading: true,
    error: null,
    lastActivity: Date.now(),
  });

  // Update last activity time
  const updateLastActivity = useCallback(() => {
    setState(prev => ({ ...prev, lastActivity: Date.now() }));
  }, []);

  // Check for session timeout
  useEffect(() => {
    const checkSessionTimeout = () => {
      const now = Date.now();
      const timeSinceLastActivity = now - state.lastActivity;

      if (state.user && timeSinceLastActivity >= SESSION_TIMEOUT) {
        logout();
        router.push('/login?timeout=true');
      }
    };

    const interval = setInterval(checkSessionTimeout, ACTIVITY_CHECK_INTERVAL);

    // Add event listeners for user activity
    ACTIVITY_EVENTS.forEach(event => {
      window.addEventListener(event, updateLastActivity);
    });

    return () => {
      clearInterval(interval);
      ACTIVITY_EVENTS.forEach(event => {
        window.removeEventListener(event, updateLastActivity);
      });
    };
  }, [state.lastActivity, state.user, router, updateLastActivity]);

  const login = async (credentials: { email: string; password: string }) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.message || 'Login failed');
      }

      const { user, token } = await response.json() as AuthResponse;
      setState({
        user,
        token,
        isLoading: false,
        error: null,
        lastActivity: Date.now(),
      });

      return { success: true };
    } catch (err) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: err instanceof Error ? err.message : 'Login failed',
      }));
      return { success: false, error: err instanceof Error ? err.message : 'Login failed' };
    }
  };

  const loginWithFace = async (faceData: FormData) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    try {
      const response = await fetch('/api/auth/login/face', {
        method: 'POST',
        body: faceData,
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.message || 'Face recognition failed');
      }

      const { user, token } = await response.json() as AuthResponse;
      setState({
        user,
        token,
        isLoading: false,
        error: null,
        lastActivity: Date.now(),
      });

      return { success: true };
    } catch (err) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: err instanceof Error ? err.message : 'Face recognition failed',
      }));
      return { success: false, error: err instanceof Error ? err.message : 'Face recognition failed' };
    }
  };

  const register = async (data: RegisterData) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Registration failed');
      }

      const { user, token } = await response.json() as AuthResponse;
      setState({
        user,
        token,
        isLoading: false,
        error: null,
        lastActivity: Date.now(),
      });

      return { success: true };
    } catch (err) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: err instanceof Error ? err.message : 'Registration failed',
      }));
      return { success: false, error: err instanceof Error ? err.message : 'Registration failed' };
    }
  };

  const logout = () => {
    setState({
      user: null,
      token: null,
      isLoading: false,
      error: null,
      lastActivity: Date.now(),
    });
    router.push('/login');
  };

  return {
    user: state.user,
    token: state.token,
    isLoading: state.isLoading,
    error: state.error,
    login,
    loginWithFace,
    register,
    logout,
  };
}

export function useRequireAuth() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login');
    }
  }, [user, isLoading, router]);

  return { user, isLoading };
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
  return user.zones?.includes(zoneId) || false;
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

  if (!user || !user.zones?.includes(zoneId)) {
    router.push('/unauthorized');
  }

  return user;
} 