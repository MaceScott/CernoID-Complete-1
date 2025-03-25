export interface User {
  id: string;
  email: string;
  name: string;
  role: 'ADMIN' | 'USER' | 'SECURITY';
  active: boolean;
  createdAt: string;
  updatedAt: string;
  lastLogin?: string;
  preferences?: Record<string, unknown>;
  accessHistory?: Record<string, unknown>;
}

export interface UserCredentials {
  email: string;
  password: string;
}

export interface UserProfile extends Omit<User, 'password'> {
  zones: string[];
  permissions: string[];
} 