/// <reference types="node" />
import { jwtVerify, JWTPayload } from 'jose';
import { User } from '@/types/user';

const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';

interface JWTUser extends JWTPayload {
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

export async function verifyToken(token: string): Promise<User | null> {
  try {
    const encoder = new TextEncoder();
    const { payload } = await jwtVerify(
      token,
      encoder.encode(JWT_SECRET)
    );

    // Type guard to verify the payload has the required properties
    const isJWTUser = (payload: JWTPayload): payload is JWTUser => {
      return (
        typeof (payload as JWTUser).id === 'string' &&
        typeof (payload as JWTUser).email === 'string' &&
        typeof (payload as JWTUser).role === 'string' &&
        typeof (payload as JWTUser).active === 'boolean' &&
        typeof (payload as JWTUser).createdAt === 'string' &&
        typeof (payload as JWTUser).updatedAt === 'string'
      );
    };

    if (!isJWTUser(payload)) {
      throw new Error('Invalid token payload');
    }

    return {
      id: payload.id,
      email: payload.email,
      name: payload.name,
      role: payload.role,
      active: payload.active,
      createdAt: payload.createdAt,
      updatedAt: payload.updatedAt,
      lastLogin: payload.lastLogin,
      preferences: payload.preferences,
      accessHistory: payload.accessHistory
    };
  } catch (error) {
    console.error('Token verification error:', error);
    return null;
  }
} 