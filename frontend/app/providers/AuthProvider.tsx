'use client';

import { createContext, useState, useEffect, type ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import type { User, AuthState, LoginCredentials, RegisterData, AuthContextType } from '@/lib/auth/types';

export const AuthContext = createContext<AuthContextType | null>(null);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const router = useRouter();
  const [state, setState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
    error: null,
  });

  const setError = (error: string | null) => {
    setState(prev => ({ ...prev, error }));
  };

  const login = async (user: User) => {
    try {
      setError(null);
      setState(prev => ({ ...prev, isLoading: true }));
      
      setState(prev => ({
        ...prev,
        user,
        isAuthenticated: true,
        isLoading: false,
      }));
      
      router.push('/dashboard');
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Login failed',
      }));
      throw error;
    }
  };

  const loginWithFace = async (faceData: string) => {
    try {
      setError(null);
      setState(prev => ({ ...prev, isLoading: true }));

      const response = await fetch('/api/auth/login/face', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ faceData }),
      });

      if (!response.ok) {
        throw new Error('Face recognition login failed');
      }

      const data = await response.json();
      if (!data.success || !data.data?.user) {
        throw new Error(data.error || 'Face recognition login failed');
      }

      setState(prev => ({
        ...prev,
        user: data.data.user,
        isAuthenticated: true,
        isLoading: false,
      }));
      
      router.push('/dashboard');
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Face recognition login failed',
      }));
      throw error;
    }
  };

  const register = async (data: RegisterData) => {
    try {
      setError(null);
      setState(prev => ({ ...prev, isLoading: true }));
      
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error('Registration failed');
      }

      const responseData = await response.json();
      if (!responseData.success || !responseData.data?.user) {
        throw new Error(responseData.error || 'Registration failed');
      }
      
      setState(prev => ({
        ...prev,
        user: responseData.data.user,
        isAuthenticated: true,
        isLoading: false,
      }));
      
      router.push('/dashboard');
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Registration failed',
      }));
      throw error;
    }
  };

  const logout = async () => {
    try {
      setError(null);
      setState(prev => ({ ...prev, isLoading: true }));
      
      await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include',
      });
      
      setState({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      });
      
      router.push('/login');
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Logout failed',
      }));
    }
  };

  const resetPassword = async (email: string) => {
    try {
      setError(null);
      setState(prev => ({ ...prev, isLoading: true }));
      
      const response = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ email }),
      });

      if (!response.ok) {
        throw new Error('Password reset failed');
      }

      const data = await response.json();
      if (!data.success) {
        throw new Error(data.error || 'Password reset failed');
      }
      
      setState(prev => ({ ...prev, isLoading: false }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Password reset failed',
      }));
      throw error;
    }
  };

  const updatePassword = async (token: string, password: string, confirmPassword: string) => {
    try {
      setError(null);
      setState(prev => ({ ...prev, isLoading: true }));
      
      const response = await fetch('/api/auth/update-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ token, password, confirmPassword }),
      });

      if (!response.ok) {
        throw new Error('Password update failed');
      }

      const data = await response.json();
      if (!data.success) {
        throw new Error(data.error || 'Password update failed');
      }
      
      setState(prev => ({ ...prev, isLoading: false }));
      router.push('/login');
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Password update failed',
      }));
      throw error;
    }
  };

  useEffect(() => {
    async function checkAuth() {
      try {
        const response = await fetch('/api/auth/me', {
          method: 'GET',
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error('Authentication check failed');
        }

        const data = await response.json();
        if (data.success && data.data?.user) {
          setState({
            user: data.data.user,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } else {
          setState({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
        }
      } catch (error) {
        setState({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: error instanceof Error ? error.message : 'Authentication check failed',
        });
      }
    }

    checkAuth();
  }, []);

  const value: AuthContextType = {
    ...state,
    login,
    loginWithFace,
    register,
    logout,
    resetPassword,
    updatePassword,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
} 