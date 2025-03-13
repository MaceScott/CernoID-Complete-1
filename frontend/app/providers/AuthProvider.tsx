'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import type { User } from '@/types/auth';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  login: (credentials: { email: string; password: string }) => Promise<{ success: boolean; error?: string }>;
  loginWithFace: (faceData: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
  register: (data: { email: string; password: string; name: string }) => Promise<{ success: boolean; error?: string }>;
  resetPassword: (email: string) => Promise<{ success: boolean; error?: string }>;
  updatePassword: (token: string, password: string, confirmPassword: string) => Promise<void>;
  updateProfile: (data: { name?: string; email?: string }) => Promise<{ success: boolean; error?: string }>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Check authentication status on mount
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const response = await fetch('/api/auth/me', {
        credentials: 'include',
      });
      
      if (response.ok) {
        const data = await response.json();
        setUser(data.user);
      } else {
        setUser(null);
      }
    } catch (err) {
      console.error('Auth check failed:', err);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (credentials: { email: string; password: string }) => {
    try {
      setError(null);
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
        credentials: 'include',
      });

      const data = await response.json();

      if (response.ok && data.success && data.data?.user) {
        setUser(data.data.user);
        return { success: true };
      } else {
        const errorMessage = data.error || 'Invalid email or password';
        setError(errorMessage);
        return { success: false, error: errorMessage };
      }
    } catch (err) {
      console.error('Login failed:', err);
      const errorMessage = err instanceof Error ? err.message : 'Login failed. Please try again.';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    }
  };

  const loginWithFace = async (faceData: string) => {
    try {
      setError(null);
      const response = await fetch('/api/auth/login/face', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ faceData }),
        credentials: 'include',
      });

      const data = await response.json();

      if (response.ok && data.success && data.data?.user) {
        setUser(data.data.user);
        return { success: true };
      } else {
        const errorMessage = data.error || 'Face recognition failed';
        setError(errorMessage);
        return { success: false, error: errorMessage };
      }
    } catch (err) {
      console.error('Face login failed:', err);
      const errorMessage = err instanceof Error ? err.message : 'Face recognition failed. Please try again.';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    }
  };

  const logout = async () => {
    try {
      setError(null);
      const response = await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include',
      });

      if (response.ok) {
        setUser(null);
        router.replace('/login');
      } else {
        throw new Error('Logout failed');
      }
    } catch (err) {
      console.error('Logout failed:', err);
      setError('Logout failed. Please try again.');
    }
  };

  const register = async (data: { email: string; password: string; name: string }) => {
    try {
      setError(null);
      setLoading(true);
      
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
      
      setUser(responseData.data.user);
      router.push('/dashboard');
      return responseData;
    } catch (error) {
      setLoading(false);
      setError(error instanceof Error ? error.message : 'Registration failed');
      throw error;
    }
  };

  const resetPassword = async (email: string) => {
    try {
      setError(null);
      setLoading(true);

      const response = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      if (!response.ok) {
        throw new Error('Password reset failed');
      }

      const data = await response.json();
      if (!data.success) {
        throw new Error(data.error || 'Password reset failed');
      }

      setLoading(false);
      return data;
    } catch (error) {
      setLoading(false);
      setError(error instanceof Error ? error.message : 'Password reset failed');
      throw error;
    }
  };

  const updatePassword = async (token: string, password: string, confirmPassword: string) => {
    try {
      setError(null);
      setLoading(true);
      
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
      
      setLoading(false);
      router.push('/login');
    } catch (error) {
      setLoading(false);
      setError(error instanceof Error ? error.message : 'Password update failed');
      throw error;
    }
  };

  const updateProfile = async (data: { name?: string; email?: string }) => {
    try {
      setError(null);
      setLoading(true);

      const response = await fetch('/api/auth/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error('Profile update failed');
      }

      const responseData = await response.json();
      if (!responseData.success || !responseData.data?.user) {
        throw new Error(responseData.error || 'Profile update failed');
      }

      setUser(responseData.data.user);
      setLoading(false);

      return responseData;
    } catch (error) {
      setLoading(false);
      setError(error instanceof Error ? error.message : 'Profile update failed');
      throw error;
    }
  };

  const value: AuthContextType = {
    user,
    loading,
    error,
    login,
    loginWithFace,
    logout,
    register,
    resetPassword,
    updatePassword,
    updateProfile,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
} 