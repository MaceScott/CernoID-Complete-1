import { BaseEntity } from '../shared';

export interface Camera extends BaseEntity {
  name: string;
  type: string;
  location: string;
  status: 'active' | 'inactive' | 'maintenance';
  zoneId: string;
  zone?: {
    id: string;
    name: string;
    level: number;
  };
  settings?: Record<string, unknown>;
  alerts?: Alert[];
}

export interface Alert extends BaseEntity {
  type: string;
  severity: 'low' | 'medium' | 'high';
  message: string;
  status: 'open' | 'resolved' | 'dismissed';
  cameraId?: string;
  camera?: {
    id: string;
    name: string;
    type: string;
    location: string;
    status: string;
  };
  userId: string;
  user?: {
    id: string;
    name: string;
    email: string;
  };
  resolvedAt?: string;
  resolvedBy?: string;
} 