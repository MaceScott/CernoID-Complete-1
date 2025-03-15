/**
 * File: route.ts (login)
 * Purpose: Implements the traditional email/password login endpoint.
 * 
 * Key Features:
 * - Request validation using zod
 * - JWT token generation and management
 * - Secure cookie management
 * - Rate limiting and security
 * - CORS support
 * 
 * Dependencies:
 * - next/server: Next.js server utilities
 * - zod: Request validation
 * - Environment variables:
 *   - BACKEND_URL: Backend API URL
 *   - NEXT_PUBLIC_APP_URL: Application URL for CORS
 */

import { NextRequest, NextResponse } from "next/server"
import { z } from "zod"
import { auth_service } from "../../../../core/security/security/auth"
import { cookies } from 'next/headers'

// Get environment variables
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
const origin = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';

/**
 * Login request validation schema
 * Ensures email and password meet security requirements
 */
const loginSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
})

/**
 * POST /api/auth/login
 * Handles user authentication via email/password
 * 
 * @param request - HTTP request object containing email and password
 * @returns NextResponse with user data and session cookie, or error
 */
export async function POST(req: NextRequest) {
  console.log('[Login API] Received login request');
  try {
    const body = await req.json();
    console.log('[Login API] Request body:', { email: body.email });
    
    // Validate request body
    const result = loginSchema.safeParse(body);
    if (!result.success) {
      console.log('[Login API] Validation failed:', result.error.issues);
      return NextResponse.json(
        { success: false, error: "Invalid input", details: result.error.issues },
        { status: 400 }
      );
    }

    const { email, password } = result.data;

    // Authenticate user
    console.log('[Login API] Authenticating user');
    const authenticated = await auth_service.authenticate_user(email, password);
    if (!authenticated) {
      console.log('[Login API] Authentication failed');
      return NextResponse.json(
        { success: false, error: "Invalid credentials" },
        { status: 401 }
      );
    }

    // Check if user is active
    if (!authenticated.is_active) {
      console.log('[Login API] User account inactive');
      return NextResponse.json(
        { success: false, error: "Account is inactive" },
        { status: 403 }
      );
    }

    // Generate tokens
    console.log('[Login API] Generating tokens');
    const tokens = await auth_service.create_tokens(authenticated);

    // Create the response
    const responseData = {
      success: true,
      user: {
        id: authenticated.id,
        email: authenticated.email,
        username: authenticated.username,
        role: authenticated.role,
        permissions: authenticated.permissions,
        last_login: authenticated.last_login
      },
      ...tokens
    };
    console.log('[Login API] Sending successful response');

    // Set session cookie
    cookies().set({
      name: 'session',
      value: tokens.access_token,
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      path: '/',
      maxAge: 60 * 60 * 24 // 24 hours
    });
    console.log('[Login API] Session cookie set');

    return NextResponse.json(responseData, { status: 200 });

  } catch (error) {
    console.error('[Login API] Error:', error);
    return NextResponse.json(
      { success: false, error: "Internal server error" },
      { status: 500 }
    );
  }
}

/**
 * GET /api/auth/login
 * Handles GET requests with a proper error
 * 
 * @returns NextResponse with error message
 */
export async function GET() {
  return NextResponse.json(
    { success: false, error: "Method not allowed" },
    { status: 405 }
  )
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
        'Access-Control-Allow-Origin': origin,
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Allow-Credentials': 'true',
      }
    }
  )
} 