/**
 * File: route.ts (face login)
 * Purpose: Implements facial recognition login endpoint.
 * 
 * Key Features:
 * - Face image data validation
 * - JWT token generation
 * - Secure cookie management
 * - CORS support
 * 
 * Dependencies:
 * - next/server: Next.js server utilities
 * - zod: Request validation
 * - jsonwebtoken: JWT token generation
 * - Environment variables:
 *   - JWT_SECRET: Secret key for JWT signing
 * 
 * Note: Current implementation is a demo that simulates face recognition.
 * In production, this should be replaced with a proper face recognition service.
 * 
 * Endpoints:
 * POST /api/auth/login/face
 * - Validates face image data
 * - Returns user data and sets session cookie
 * 
 * OPTIONS /api/auth/login/face
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
 * Face login request validation schema
 * Expects base64 encoded image data
 */
const faceLoginSchema = z.object({
  imageData: z.string(),
});

/**
 * POST /api/auth/login/face
 * Handles user authentication via facial recognition
 * 
 * @param request - HTTP request object containing face image data
 * @returns NextResponse with user data and session cookie, or error
 */
export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { imageData } = faceLoginSchema.parse(body);

    // For demo purposes, we'll simulate face recognition
    // In production, you would use a proper face recognition service
    const isRecognized = true;

    if (!isRecognized) {
      return NextResponse.json(
        { success: false, error: 'Face not recognized' },
        { status: 401 }
      );
    }

    // Create session token with user claims
    const sessionToken = sign(
      {
        userId: '1',
        email: 'admin@cernoid.com',
        name: 'Admin User',
        role: 'admin',
        permissions: ['all'],
      },
      JWT_SECRET,
      { expiresIn: '24h' }
    );

    // Set secure session cookie
    cookies().set({
      name: 'session',
      value: sessionToken,
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      path: '/',
      maxAge: 60 * 60 * 24, // 24 hours
    });

    return NextResponse.json(
      {
        success: true,
        user: {
          id: '1',
          email: 'admin@cernoid.com',
          name: 'Admin User',
          role: 'admin',
          permissions: ['all'],
        },
      },
      { status: 200 }
    );
  } catch (error) {
    console.error('Face login error:', error);
    return NextResponse.json(
      { success: false, error: 'Face login failed' },
      { status: 500 }
    );
  }
}

/**
 * OPTIONS /api/auth/login/face
 * Handles CORS preflight requests with credentials support
 * 
 * @returns NextResponse with CORS headers
 */
export async function OPTIONS() {
  return NextResponse.json({}, {
    headers: {
      'Access-Control-Allow-Credentials': 'true',
      'Access-Control-Allow-Origin': origin,
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    }
  });
} 