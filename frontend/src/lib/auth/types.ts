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
  permissions: Permission[];
  zones: SecurityZone[];
  metadata?: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
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
  remember?: boolean;
}

export interface RegisterData extends LoginCredentials {
  name: string;
  confirmPassword: string;
}

export interface AuthResponse {
  user: User;
  token: string;
}

export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
} 