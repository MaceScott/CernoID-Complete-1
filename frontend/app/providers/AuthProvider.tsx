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

import { createContext, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { User, AuthContextType, LoginCredentials, ApiResponse, AuthResponse, RegisterData } from '@/lib/auth/types';

export const AuthContext = createContext<AuthContextType>({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
  login: async () => ({ success: false }),
  loginWithFace: async () => ({ success: false }),
  logout: async () => {},
  checkAuth: async () => {},
  register: async () => ({ success: false }),
  resetPassword: async () => ({ success: false }),
  updateProfile: async () => ({ success: false }),
});

/**
 * AuthProvider Component
 * 
 * Provides authentication context to the application, managing user sessions,
 * authentication state, and related operations. Handles automatic authentication
 * checks and protected route redirections.
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const checkAuth = async () => {
    try {
      const response = await fetch('/api/auth/me', {
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        setUser(data.user);
        
        // Only redirect if we're on the login page
        if (window.location.pathname === '/login') {
          router.replace('/dashboard');
        }
      } else {
        setUser(null);
        if (window.location.pathname !== '/login' && 
            window.location.pathname !== '/register' && 
            window.location.pathname !== '/forgot-password') {
          router.replace('/login');
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to check authentication');
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (credentials: LoginCredentials): Promise<ApiResponse<AuthResponse>> => {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
        credentials: 'include',
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setUser(data.user);
        setError(null);
        // Use replace instead of push to prevent back navigation to login
        router.replace('/dashboard');
        return { success: true, data };
      } else {
        setError(data.error || 'Login failed');
        return { success: false, error: data.error };
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Login failed';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    }
  };

  const loginWithFace = async (faceData: string): Promise<ApiResponse<AuthResponse>> => {
    try {
      const response = await fetch('/api/auth/login/face', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ faceData }),
        credentials: 'include',
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setUser(data.user);
        setError(null);
        // Use replace instead of push to prevent back navigation to login
        router.replace('/dashboard');
        return { success: true, data };
      } else {
        setError(data.error || 'Face login failed');
        return { success: false, error: data.error };
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Face login failed';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    }
  };

  const logout = async (): Promise<void> => {
    try {
      await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include',
      });
    } finally {
      setUser(null);
      setError(null);
      router.replace('/login');
    }
  };

  const register = async (data: RegisterData): Promise<ApiResponse<AuthResponse>> => {
    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
        credentials: 'include',
      });

      const responseData = await response.json();

      if (response.ok) {
        setUser(responseData.user);
        setError(null);
        router.replace('/dashboard');
        return { success: true, data: responseData };
      } else {
        setError(responseData.error || 'Registration failed');
        return { success: false, error: responseData.error };
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Registration failed';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    }
  };

  const resetPassword = async (email: string): Promise<ApiResponse<void>> => {
    try {
      const response = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (response.ok) {
        setError(null);
        return { success: true };
      } else {
        setError(data.error || 'Password reset failed');
        return { success: false, error: data.error };
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Password reset failed';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    }
  };

  const updateProfile = async (data: Partial<User>): Promise<ApiResponse<User>> => {
    try {
      const response = await fetch('/api/auth/profile', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
        credentials: 'include',
      });

      const responseData = await response.json();

      if (response.ok) {
        setUser(responseData.user);
        setError(null);
        return { success: true, data: responseData.user };
      } else {
        setError(responseData.error || 'Profile update failed');
        return { success: false, error: responseData.error };
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Profile update failed';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        error,
        login,
        loginWithFace,
        logout,
        checkAuth,
        register,
        resetPassword,
        updateProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
} 