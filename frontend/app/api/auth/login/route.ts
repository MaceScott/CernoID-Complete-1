/**
 * File: route.ts (login)
 * Purpose: Implements the traditional email/password login endpoint.
 * 
 * Key Features:
 * - Request validation using zod
 * - JWT token generation
 * - Secure cookie management
 * - Default admin account handling
 * - CORS support
 * 
 * Dependencies:
 * - next/server: Next.js server utilities
 * - zod: Request validation
 * - jsonwebtoken: JWT token generation
 * - Environment variables:
 *   - JWT_SECRET: Secret key for JWT signing
 *   - NEXT_PUBLIC_APP_URL: Application URL for CORS
 * 
 * Endpoints:
 * POST /api/auth/login
 * - Validates email/password
 * - Returns user data and sets session cookie
 * 
 * OPTIONS /api/auth/login
 * - Handles CORS preflight requests
 */

import { NextResponse } from 'next/server';
import { z } from 'zod';
import { cookies } from 'next/headers';
import { sign } from 'jsonwebtoken';

const JWT_SECRET = process.env.JWT_SECRET || 'default-secret-key';

if (!process.env.JWT_SECRET) {
  console.warn('Warning: Using default JWT secret. Please set JWT_SECRET environment variable in production.');
}

/**
 * Login request validation schema
 * Ensures email is valid and password is not empty
 */
const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(1, 'Password is required'),
});

// Get origin from environment or default to localhost
const origin = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';

/**
 * POST /api/auth/login
 * Handles user authentication via email/password
 * 
 * @param request - HTTP request object containing email and password
 * @returns NextResponse with user data and session cookie, or error
 */
export async function POST(request: Request) {
  try {
    const body = await request.json();
    
    // Validate request body
    const result = loginSchema.safeParse(body);
    if (!result.success) {
      return NextResponse.json(
        { 
          success: false, 
          error: 'Invalid request data',
          details: result.error.issues
        },
        { status: 400 }
      );
    }

    const { email, password } = result.data;

    // Check for default admin credentials
    if (email === 'admin@cernoid.com' && password === 'admin123') {
      const user = {
        id: '1',
        email: 'admin@cernoid.com',
        name: 'Admin User',
        role: 'admin',
        permissions: ['admin'],
        zones: [],
      };

      // Create JWT token with user claims
      const token = sign(
        { 
          sub: user.id,
          email: user.email,
          role: user.role,
          permissions: user.permissions
        },
        JWT_SECRET,
        { expiresIn: '24h' }
      );
      
      // Create response with user data
      const response = NextResponse.json(
        {
          success: true,
          data: { user }
        },
        { status: 200 }
      );

      // Set secure session cookie
      response.cookies.set({
        name: 'session',
        value: token,
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        path: '/',
        maxAge: 60 * 60 * 24, // 24 hours
      });

      return response;
    }

    // If not default admin, return error
    return NextResponse.json(
      { 
        success: false, 
        error: 'Invalid credentials'
      },
      { status: 401 }
    );
  } catch (error) {
    console.error('Login error:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: 'Internal server error'
      },
      { status: 500 }
    );
  }
}

/**
 * OPTIONS /api/auth/login
 * Handles CORS preflight requests
 * 
 * @returns NextResponse with CORS headers
 */
export async function OPTIONS() {
  return NextResponse.json(
    {},
    {
      status: 200,
      headers: {
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
      }
    }
  );
} 