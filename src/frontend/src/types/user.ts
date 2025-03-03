export interface User {
  id: string;
  username: string;
  email: string;
  firstName?: string;
  lastName?: string;
  role: 'admin' | 'user';
  permissions: string[];
  createdAt: string;
  updatedAt: string;
} 