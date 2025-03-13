import { z } from 'zod';
import { SecurityEventSchema, PermissionSchema, SecurityZoneSchema } from './schemas';

export type SecurityEvent = z.infer<typeof SecurityEventSchema>;
export type Permission = z.infer<typeof PermissionSchema>;
export type SecurityZone = z.infer<typeof SecurityZoneSchema>;

export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  permissions: string[];
  zones: string[];
  avatar?: string;
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
  name: string;
  confirmPassword: string;
}

export interface AuthResponse {
  user: User;
}

export interface ApiResponse<T> {
  success: boolean;
  error?: string;
  data?: T;
}

export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (credentials: LoginCredentials) => Promise<ApiResponse<AuthResponse>>;
  loginWithFace: (faceData: string) => Promise<ApiResponse<AuthResponse>>;
  logout: () => Promise<void>;
  register: (data: RegisterData) => Promise<ApiResponse<AuthResponse>>;
  resetPassword: (email: string) => Promise<ApiResponse<void>>;
  updateProfile: (data: Partial<User>) => Promise<ApiResponse<User>>;
} 