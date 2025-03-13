import { z } from 'zod';
import { SecurityEventSchema, PermissionSchema, SecurityZoneSchema } from './schemas';

export type SecurityEvent = z.infer<typeof SecurityEventSchema>;
export type Permission = z.infer<typeof PermissionSchema>;
export type SecurityZone = z.infer<typeof SecurityZoneSchema>;

export interface User {
  id: string;
  email: string;
  role: string;
  permissions: string[];
  zones: string[];
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData extends LoginCredentials {
  name?: string;
}

export interface AuthResponse {
  user: User;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  loginWithFace: (faceData: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
  updatePassword: (token: string, password: string, confirmPassword: string) => Promise<void>;
} 