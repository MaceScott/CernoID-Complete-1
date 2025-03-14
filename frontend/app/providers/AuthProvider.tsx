'use client';

import { createContext, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { User } from '@/types/user';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (credentials: { email: string; password: string }) => Promise<{ success: boolean; error?: string }>;
  loginWithFace: (faceData: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType>({
  user: null,
  isLoading: true,
  login: async () => ({ success: false }),
  loginWithFace: async () => ({ success: false }),
  logout: async () => {},
  checkAuth: async () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
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
      console.error('Auth check failed:', err);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (credentials: { email: string; password: string }) => {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
        credentials: 'include',
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setUser(data.user);
        // Wait for state to update
        await new Promise(resolve => setTimeout(resolve, 100));
        router.replace('/dashboard');
        return { success: true };
      }

      return { 
        success: false, 
        error: data.error || 'Login failed. Please try again.' 
      };
    } catch (err) {
      console.error('Login failed:', err);
      return { 
        success: false, 
        error: err instanceof Error ? err.message : 'Login failed. Please try again.' 
      };
    }
  };

  const loginWithFace = async (faceData: string) => {
    try {
      const response = await fetch('/api/auth/login/face', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ faceData }),
        credentials: 'include',
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setUser(data.user);
        // Wait for state to update
        await new Promise(resolve => setTimeout(resolve, 100));
        router.replace('/dashboard');
        return { success: true };
      }

      return { 
        success: false, 
        error: data.error || 'Face login failed. Please try again.' 
      };
    } catch (err) {
      console.error('Face login failed:', err);
      return { 
        success: false, 
        error: err instanceof Error ? err.message : 'Face login failed. Please try again.' 
      };
    }
  };

  const logout = async () => {
    try {
      await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include',
      });
    } catch (err) {
      console.error('Logout failed:', err);
    } finally {
      setUser(null);
      router.replace('/login');
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        login,
        loginWithFace,
        logout,
        checkAuth,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
} 