/**
 * File: types.ts
 * Purpose: Defines TypeScript types and interfaces for authentication and user management.
 * 
 * Key Features:
 * - User data structure
 * - Authentication state types
 * - API response types
 * - Login and registration data types
 * 
 * Dependencies:
 * - zod: Runtime type validation
 * - Custom schema definitions from ./schemas
 */

import { z } from 'zod';
import { SecurityEventSchema, PermissionSchema, SecurityZoneSchema } from './schemas';

// Schema-derived types for security features
export type SecurityEvent = z.infer<typeof SecurityEventSchema>;
export type Permission = z.infer<typeof PermissionSchema>;
export type SecurityZone = z.infer<typeof SecurityZoneSchema>;

/**
 * Core user data structure
 * Contains essential user information and permissions
 */
export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  permissions: string[];
  zones: string[];
  avatar?: string;
}

/**
 * Authentication state interface
 * Used to track current authentication status
 */
export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

/**
 * Login credentials interface
 * Basic email/password combination
 */
export interface LoginCredentials {
  email: string;
  password: string;
}

/**
 * Registration data interface
 * Extends login credentials with additional required fields
 */
export interface RegisterData extends LoginCredentials {
  name: string;
  confirmPassword: string;
}

/**
 * Authentication response interface
 * Contains user data after successful authentication
 */
export interface AuthResponse {
  user: User;
}

/**
 * Generic API response interface
 * Used for all authentication-related API responses
 */
export interface ApiResponse<T> {
  success: boolean;
  error?: string;
  data?: T;
}

/**
 * Authentication context interface
 * Defines all available authentication operations and state
 */
export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (credentials: LoginCredentials) => Promise<ApiResponse<AuthResponse>>;
  loginWithFace: (faceData: string) => Promise<ApiResponse<AuthResponse>>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  register: (data: RegisterData) => Promise<ApiResponse<AuthResponse>>;
  resetPassword: (email: string) => Promise<ApiResponse<void>>;
  updateProfile: (data: Partial<User>) => Promise<ApiResponse<User>>;
} 