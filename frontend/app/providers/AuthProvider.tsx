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

import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { User, AuthContextType, LoginCredentials, ApiResponse, AuthResponse, RegisterData } from '@/lib/auth/types';

// Routes that don't require authentication
const PUBLIC_ROUTES = ['/login', '/register', '/forgot-password'];

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
  clearError: () => {},
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
  const pathname = usePathname();

  // Clear error state
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Handle navigation based on auth state
  const handleNavigation = useCallback(async (isAuthenticated: boolean) => {
    const isPublicRoute = PUBLIC_ROUTES.includes(pathname);
    console.log('[AuthProvider] handleNavigation:', { 
      isAuthenticated, 
      isPublicRoute, 
      currentPath: pathname 
    });
    
    if (isAuthenticated && isPublicRoute) {
      console.log('[AuthProvider] Redirecting to dashboard');
      await router.replace('/dashboard');
      console.log('[AuthProvider] Redirect completed');
    } else if (!isAuthenticated && !isPublicRoute && pathname !== '/') {
      await router.replace('/login');
    }
  }, [pathname, router]);

  /**
   * Checks the current authentication status
   * - Fetches user data from /api/auth/me
   * - Updates authentication state
   * - Handles protected route redirections
   */
  const checkAuth = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await fetch('/api/auth/me', {
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        setUser(data.user);
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
  }, [handleNavigation]);

  /**
   * Handles traditional email/password login
   * @param {LoginCredentials} credentials - User login credentials
   * @returns {Promise<ApiResponse<AuthResponse>>} Login response with user data
   */
  const login = async (credentials: LoginCredentials): Promise<ApiResponse<AuthResponse>> => {
    try {
      console.log('[AuthProvider] Login started');
      setIsLoading(true);
      clearError();

      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
        credentials: 'include',
      });

      const data = await response.json();
      console.log('[AuthProvider] Login response:', { 
        ok: response.ok, 
        status: response.status,
        success: data.success 
      });

      if (response.ok && data.success) {
        console.log('[AuthProvider] Setting user data');
        setUser(data.user);
        console.log('[AuthProvider] Initiating navigation');
        await handleNavigation(true);
        console.log('[AuthProvider] Navigation completed');
        return { success: true, data };
      } else {
        console.log('[AuthProvider] Login failed:', data.error);
        setError(data.error || 'Login failed');
        return { success: false, error: data.error };
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Login failed';
      console.error('[AuthProvider] Login error:', errorMessage);
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handles face recognition login
   * @param {string} faceData - Base64 encoded face image data
   * @returns {Promise<ApiResponse<AuthResponse>>} Login response with user data
   */
  const loginWithFace = async (faceData: string): Promise<ApiResponse<AuthResponse>> => {
    try {
      setIsLoading(true);
      clearError();

      const response = await fetch('/api/auth/login/face', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ faceData }),
        credentials: 'include',
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setUser(data.user);
        await handleNavigation(true);
        return { success: true, data };
      } else {
        setError(data.error || 'Face login failed');
        return { success: false, error: data.error };
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Face login failed';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handles user logout
   * - Clears user session
   * - Redirects to login page
   */
  const logout = async (): Promise<void> => {
    try {
      setIsLoading(true);
      clearError();

      await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include',
      });
    } finally {
      setUser(null);
      setIsLoading(false);
      await handleNavigation(false);
    }
  };

  /**
   * Handles user registration
   * @param {RegisterData} data - User registration data
   * @returns {Promise<ApiResponse<AuthResponse>>} Registration response with user data
   */
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

  /**
   * Handles password reset request
   * @param {string} email - User email address
   * @returns {Promise<ApiResponse<void>>} Password reset response
   */
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

  /**
   * Updates user profile information
   * @param {Partial<User>} data - Updated user data
   * @returns {Promise<ApiResponse<User>>} Updated user profile
   */
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

  // Check auth status on mount and pathname change
  useEffect(() => {
    console.log("[AuthProvider] Initializing, checking session");
    checkAuth();
  }, [checkAuth]);

  const contextValue = {
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
    clearError,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
} 