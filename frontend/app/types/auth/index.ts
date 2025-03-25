import { BaseEntity } from '../shared';
import { Session } from 'next-auth';

// User types
export interface User extends BaseEntity {
  username: string;
  email: string;
  name?: string;
  role: string;
  status: 'active' | 'inactive' | 'suspended';
  isAdmin: boolean;
  accessLevel: AccessLevel;
  allowedZones: string[];
  lastLogin?: string;
}

// Access types
export type AccessLevel = 'free' | 'restricted' | 'high-security';

export interface TimeSlot {
  start: string; // HH:mm format
  end: string;   // HH:mm format
  days: number[]; // 0-6 for Sunday-Saturday
}

export interface ZoneAccess {
  zoneId: string;
  name: string;
  description: string;
  accessLevel: AccessLevel;
  allowedTimeSlots: TimeSlot[];
  restrictedTimeSlots: TimeSlot[];
  highSecurityTimeSlots: TimeSlot[];
  allowedRoles: string[];
  maxOccupancy?: number;
  currentOccupancy?: number;
}

export interface AccessAlert extends BaseEntity {
  type: 'unauthorized' | 'restricted' | 'high-security';
  zoneId: string;
  userId: string;
  userName: string;
  details: {
    attemptedAccess: string;
    currentTime: string;
    allowedTimeSlots: TimeSlot[];
    userRole: string;
    userAccessLevel: number;
  };
  status: 'active' | 'resolved' | 'dismissed';
  resolvedBy?: string;
  resolvedAt?: string;
}

export interface AccessLog extends BaseEntity {
  userId: string;
  userName: string;
  zoneId: string;
  zoneName: string;
  action: 'enter' | 'exit' | 'denied';
  accessLevel: AccessLevel;
  details: {
    timeSlot: TimeSlot;
    userRole: string;
    userAccessLevel: number;
  };
}

// Authentication types
export interface AuthResponse {
  token: string;
  refreshToken: string;
  user: User;
}

export interface LoginCredentials {
  username: string;
  password: string;
  remember?: boolean;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  name?: string;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetConfirm {
  token: string;
  newPassword: string;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

// Re-export Session type
export type { Session }; 