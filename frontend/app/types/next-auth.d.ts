import 'next-auth';

declare module 'next-auth' {
  interface User {
    id: string;
    email: string | null;
    name: string | null;
    role: string;
    isAdmin: boolean;
    accessLevel: number;
    allowedZones: string[];
    status: string;
    createdAt: Date;
    updatedAt: Date;
    lastLogin: Date | null;
  }

  interface Session {
    user: {
      id: string;
      email?: string | null;
      name?: string | null;
      role: string;
      isAdmin: boolean;
      accessLevel: number;
      allowedZones: string[];
    }
  }

  interface JWT {
    role: string;
    isAdmin: boolean;
    accessLevel: number;
    allowedZones: string[];
  }
} 