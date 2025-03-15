/**
 * File: types.ts
 * Purpose: Defines TypeScript types and interfaces for authentication and user management.
 * 
 * Key Features:
 * - User data structure
 * - Authentication state types
 * - API response types
 * - Login and registration data types
 * - Security event and permission types
 * 
 * Dependencies:
 * - zod: Runtime type validation
 * - Custom schema definitions from ./schemas
 * 
 * Usage:
 * - Used by AuthProvider for state management
 * - Used by LoginForm for form handling
 * - Used by API routes for request/response typing
 */

import { z } from 'zod';
import { SecurityEventSchema, PermissionSchema, SecurityZoneSchema } from './schemas';

/**
 * Security Event Type
 * Represents a security-related event in the system
 * Derived from SecurityEventSchema
 */
export type SecurityEvent = z.infer<typeof SecurityEventSchema>;

/**
 * Permission Type
 * Defines user permissions and access levels
 * Derived from PermissionSchema
 */
export type Permission = z.infer<typeof PermissionSchema>;

/**
 * Security Zone Type
 * Represents a security zone or area in the system
 * Derived from SecurityZoneSchema
 */
export type SecurityZone = z.infer<typeof SecurityZoneSchema>;

/**
 * Core user data structure
 * Contains essential user information and permissions
 * 
 * @property {string} id - Unique user identifier
 * @property {string} email - User's email address
 * @property {string} name - User's full name
 * @property {string} role - User's role in the system
 * @property {string[]} permissions - List of user permissions
 * @property {string[]} zones - List of security zones user has access to
 * @property {string} [avatar] - Optional user avatar URL
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
 * 
 * @property {User | null} user - Current user data or null if not authenticated
 * @property {boolean} isAuthenticated - Whether user is currently authenticated
 * @property {boolean} isLoading - Whether authentication state is being checked
 * @property {string | null} error - Any authentication error message
 */
export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

/**
 * Login credentials interface
 * Basic email/password combination for traditional login
 * 
 * @property {string} email - User's email address
 * @property {string} password - User's password
 */
export interface LoginCredentials {
  email: string;
  password: string;
}

/**
 * Registration data interface
 * Extends login credentials with additional required fields
 * 
 * @property {string} name - User's full name
 * @property {string} confirmPassword - Password confirmation
 * @extends LoginCredentials
 */
export interface RegisterData extends LoginCredentials {
  name: string;
  confirmPassword: string;
}

/**
 * Authentication response interface
 * Contains user data after successful authentication
 * 
 * @property {User} user - Authenticated user data
 */
export interface AuthResponse {
  user: User;
}

/**
 * Generic API response interface
 * Used for all authentication-related API responses
 * 
 * @template T - Type of data returned in successful response
 * @property {boolean} success - Whether the operation was successful
 * @property {string} [error] - Error message if operation failed
 * @property {T} [data] - Response data if operation succeeded
 */
export interface ApiResponse<T> {
  success: boolean;
  error?: string;
  data?: T;
}

/**
 * Authentication context interface
 * Defines all available authentication operations and state
 * Used by AuthProvider to provide authentication context
 * 
 * @property {User | null} user - Current user data
 * @property {boolean} isAuthenticated - Authentication status
 * @property {boolean} isLoading - Loading state
 * @property {string | null} error - Error state
 * @property {Function} login - Traditional login function
 * @property {Function} loginWithFace - Face recognition login function
 * @property {Function} logout - Logout function
 * @property {Function} checkAuth - Authentication check function
 * @property {Function} register - User registration function
 * @property {Function} resetPassword - Password reset function
 * @property {Function} updateProfile - Profile update function
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