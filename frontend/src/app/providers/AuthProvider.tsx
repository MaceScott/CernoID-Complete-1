'use client';

import { createContext, useState, useEffect, type ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import type { User, AuthState, LoginCredentials, RegisterData } from '@/lib/auth/types';
import * as authService from '@/lib/auth/service';

interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  loginWithFace: (faceData: Blob) => Promise<void>;
  logout: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
  updatePassword: (token: string, password: string, confirmPassword: string) => Promise<void>;
}

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

  const login = async (credentials: LoginCredentials) => {
    try {
      setError(null);
      setState(prev => ({ ...prev, isLoading: true }));
      
      const response = await authService.login(credentials);
      const user = response.data?.user;
      if (!response.success || !user) {
        throw new Error(response.error || 'Login failed');
      }
      
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

  const register = async (data: RegisterData) => {
    try {
      setError(null);
      setState(prev => ({ ...prev, isLoading: true }));
      
      const response = await authService.register(data);
      const user = response.data?.user;
      if (!response.success || !user) {
        throw new Error(response.error || 'Registration failed');
      }
      
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
        error: error instanceof Error ? error.message : 'Registration failed',
      }));
      throw error;
    }
  };

  const loginWithFace = async (faceData: Blob) => {
    try {
      setError(null);
      setState(prev => ({ ...prev, isLoading: true }));
      
      // Convert Blob to base64
      const reader = new FileReader();
      const base64Promise = new Promise<string>((resolve, reject) => {
        reader.onload = () => {
          if (typeof reader.result === 'string') {
            // Remove data URL prefix (e.g., "data:image/jpeg;base64,")
            const base64String = reader.result.split(',')[1];
            resolve(base64String);
          } else {
            reject(new Error('Failed to convert image to base64'));
          }
        };
        reader.onerror = () => reject(reader.error);
      });
      
      reader.readAsDataURL(faceData);
      const base64Data = await base64Promise;

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/login/face`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ faceData: base64Data }),
      });

      if (!response.ok) {
        throw new Error('Face recognition login failed');
      }

      const data = await response.json();
      setState(prev => ({
        ...prev,
        user: data.user,
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

  const logout = async () => {
    try {
      setError(null);
      setState(prev => ({ ...prev, isLoading: true }));
      
      await authService.logout();
      
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
      
      const response = await authService.resetPassword(email);
      if (!response.success) {
        throw new Error(response.error || 'Password reset failed');
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
      
      const response = await authService.updatePassword(token, password, confirmPassword);
      if (!response.success) {
        throw new Error(response.error || 'Password update failed');
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
        const response = await authService.getCurrentUser();
        const user = response.data?.user;
        if (response.success && user) {
          setState({
            user,
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