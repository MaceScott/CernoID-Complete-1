import { User } from './user';

export interface TimeSlot {
  id: string;
  start: string;
  end: string;
  days: number[];
}

export interface ZoneAccess {
  id: string;
  name: string;
  description?: string;
  timeSlots: TimeSlot[];
  users: User[];
}

export interface AccessAlert {
  id: string;
  timestamp: string;
  type: 'UNAUTHORIZED_ACCESS' | 'SUSPICIOUS_ACTIVITY' | 'DOOR_FORCED' | 'OTHER';
  description: string;
  zoneId?: string;
  userId?: string;
  resolved: boolean;
  priority: 'LOW' | 'MEDIUM' | 'HIGH';
}

export interface AccessLog {
  id: string;
  timestamp: string;
  type: 'ENTRY' | 'EXIT' | 'ATTEMPT';
  success: boolean;
  userId: string;
  zoneId: string;
  description?: string;
} 