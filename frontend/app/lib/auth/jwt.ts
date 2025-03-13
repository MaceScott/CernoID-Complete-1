import { jwtVerify, JWTPayload } from 'jose';
import { User } from './types';

const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';

interface JWTUser extends JWTPayload {
  id: string;
  email: string;
  name: string;
  role: string;
  permissions: string[];
  zones: string[];
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
        Array.isArray((payload as JWTUser).permissions) &&
        Array.isArray((payload as JWTUser).zones)
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
      permissions: payload.permissions,
      zones: payload.zones
    };
  } catch (error) {
    console.error('Token verification error:', error);
    return null;
  }
} 