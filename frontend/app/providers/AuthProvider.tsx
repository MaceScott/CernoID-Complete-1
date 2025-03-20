/**
 * File: AuthProvider.tsx
 * Purpose: Provides authentication context and state management for the entire application.
 * 
 * Key Features:
 * - Global authentication state management
 * - User session handling
 * - Authentication methods (login, logout, register)
 * - Profile management
 * - Protected route handling
 * 
 * Dependencies:
 * - next/navigation: Routing
 * - React Context API: State management
 * - Custom auth types from @/lib/auth/types
 * 
 * API Endpoints Used:
 * - /api/auth/me: Check authentication status
 * - /api/auth/login: Traditional login
 * - /api/auth/login/face: Face recognition login
 * - /api/auth/logout: User logout
 * - /api/auth/register: User registration
 * - /api/auth/reset-password: Password reset
 * - /api/auth/profile: Profile updates
 * 
 * Expected Outputs:
 * - Authentication state
 * - User data
 * - Loading states
 * - Error messages
 */

'use client';

import { ReactNode, createContext, useContext, useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { loggingService } from '../lib/logging-service';
import { User, ApiResponse } from '../types/shared';
import { apiClient } from '../lib/api-client';

// Routes that don't require authentication
const PUBLIC_ROUTES = [
  '/login',
  '/register',
  '/forgot-password',
  '/unauthorized'
];

interface AuthResponse {
  user: User;
  token: string;
}

interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  isLoading: boolean;
  error: string | null;
  login: (credentials: { email: string; password: string }) => Promise<void>;
  loginWithFace: (faceData: string) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuthContext() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuthContext must be used within an AuthProvider');
  }
  return context;
}

interface AuthProviderProps {
  children: ReactNode;
}

/**
 * AuthProvider Component
 * 
 * Provides authentication context to the application, managing user sessions,
 * authentication state, and related operations. Handles automatic authentication
 * checks and protected route redirections.
 */
export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const pathname = usePathname();

  const clearError = () => setError(null);

  const handleNavigation = async (isAuthenticated: boolean) => {
    const isPublicRoute = PUBLIC_ROUTES.some(route => pathname.startsWith(route));
    loggingService.debug('Handling navigation', { isAuthenticated, isPublicRoute, pathname });

    if (isAuthenticated && isPublicRoute) {
      await router.replace('/dashboard');
    } else if (!isAuthenticated && !isPublicRoute && pathname !== '/') {
      await router.replace('/login');
    }
  };

  const checkAuth = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get<AuthResponse>('/api/auth/me');

      if (response.success && response.data) {
        setUser(response.data.user);
        await handleNavigation(true);
      } else {
        setUser(null);
        await handleNavigation(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to check authentication');
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (credentials: { email: string; password: string }) => {
    try {
      setIsLoading(true);
      clearError();

      const response = await apiClient.post<AuthResponse>('/api/auth/login', credentials);

      if (response.success && response.data) {
        setUser(response.data.user);
        await handleNavigation(true);
      } else {
        setError(response.error || 'Login failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const loginWithFace = async (faceData: string) => {
    try {
      setIsLoading(true);
      clearError();

      const response = await apiClient.post<AuthResponse>('/api/auth/login/face', { faceData });

      if (response.success && response.data) {
        setUser(response.data.user);
        await handleNavigation(true);
      } else {
        setError(response.error || 'Face login failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Face login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      setIsLoading(true);
      clearError();

      await apiClient.post('/api/auth/logout');
    } finally {
      setUser(null);
      await handleNavigation(false);
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loggingService.debug('Auth provider mounted');
    checkAuth();
  }, []);

  const contextValue: AuthContextType = {
    isAuthenticated: !!user,
    user,
    isLoading,
    error,
    login,
    loginWithFace,
    logout,
    clearError,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
} 