export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'user' | 'security';
  status: 'active' | 'inactive' | 'suspended';
  isAdmin: boolean;
  accessLevel: number;
  allowedZones: string[];
  permissions: string[];
  lastLogin: string | null;
  lastAccess: string | null;
  avatar?: string;
  accessHistory: {
    timestamp: string;
    action: string;
    location: string;
  }[];
  preferences: {
    theme: 'light' | 'dark';
    notifications: boolean;
    timezone: string;
  };
  createdAt: string;
  updatedAt: string;
} 