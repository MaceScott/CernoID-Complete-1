import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';
import { sign } from 'jsonwebtoken';

const JWT_SECRET = process.env.JWT_SECRET || 'default-secret-key';
const origin = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';

if (!process.env.JWT_SECRET) {
  console.warn('Warning: Using default JWT secret. Please set JWT_SECRET environment variable in production.');
}

export interface UserData {
  id: string;
  email: string;
  username?: string;
  name?: string;
  role: string;
  permissions?: string[];
  last_login?: string;
}

export function createSessionToken(userData: UserData): string {
  return sign(userData, JWT_SECRET, { expiresIn: '24h' });
}

export function setSessionCookie(response: NextResponse, token: string): NextResponse {
  response.cookies.set({
    name: 'session',
    value: token,
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    path: '/',
    maxAge: 60 * 60 * 24 // 24 hours
  });
  return response;
}

export function createSuccessResponse(data: any, status: number = 200): NextResponse {
  return NextResponse.json(
    { success: true, ...data },
    { status }
  );
}

export function createErrorResponse(error: string, status: number = 500, details?: any): NextResponse {
  return NextResponse.json(
    { success: false, error, ...(details && { details }) },
    { status }
  );
}

export function createCorsResponse(): NextResponse {
  return NextResponse.json(
    {},
    {
      status: 200,
      headers: {
        'Access-Control-Allow-Origin': origin,
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Allow-Credentials': 'true',
      }
    }
  );
} 