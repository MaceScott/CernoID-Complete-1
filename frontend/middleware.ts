/**
 * File: middleware.ts
 * Purpose: Implements route protection and authentication middleware for Next.js application.
 * 
 * Key Features:
 * - Route protection based on JWT authentication
 * - Public route allowlist
 * - Session token validation
 * - User context propagation to API routes
 * 
 * Dependencies:
 * - next/server: Next.js server utilities
 * - jsonwebtoken: JWT validation
 * - Environment variables:
 *   - JWT_SECRET: Secret key for JWT validation
 * 
 * Protected Routes:
 * - All routes except those in publicRoutes array
 * - Static assets and public folder are excluded
 */

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { verify } from 'jsonwebtoken';

const JWT_SECRET = process.env.JWT_SECRET || 'default-secret-key';

if (!process.env.JWT_SECRET) {
  console.warn('Warning: Using default JWT secret. Please set JWT_SECRET environment variable in production.');
}

/**
 * List of public routes that don't require authentication
 * Includes auth-related endpoints and public pages
 */
const publicRoutes = [
  '/',
  '/login',
  '/register',
  '/forgot-password',
  '/api/auth/login',
  '/api/auth/login/face',
  '/api/auth/register',
  '/api/auth/forgot-password',
];

/**
 * Checks if a given path matches any public route
 * @param path - The route path to check
 * @returns boolean indicating if the route is public
 */
const isPublicRoute = (path: string) => {
  return publicRoutes.some(route => path.startsWith(route));
};

/**
 * Middleware function for route protection and authentication
 * Handles:
 * 1. Public route access
 * 2. Session token validation
 * 3. User context propagation
 * 4. Protected route access
 */
export async function middleware(request: NextRequest) {
  const path = request.nextUrl.pathname;

  // Allow public routes without authentication
  if (isPublicRoute(path)) {
    return NextResponse.next();
  }

  // Get session token from cookies
  const sessionToken = request.cookies.get('session')?.value;

  if (!sessionToken) {
    // Redirect to login if no session token is present
    const loginUrl = new URL('/login', request.url);
    return NextResponse.redirect(loginUrl);
  }

  try {
    // Verify the JWT token
    const decoded = verify(sessionToken, JWT_SECRET);
    
    // Add user info to headers for backend routes
    if (path.startsWith('/api/')) {
      const requestHeaders = new Headers(request.headers);
      requestHeaders.set('x-user-id', (decoded as any).userId);
      requestHeaders.set('x-user-role', (decoded as any).role);
      
      return NextResponse.next({
        request: {
          headers: requestHeaders,
        },
      });
    }

    // Continue to protected routes
    return NextResponse.next();
  } catch (error) {
    // If token is invalid, redirect to login
    const loginUrl = new URL('/login', request.url);
    return NextResponse.redirect(loginUrl);
  }
}

/**
 * Middleware configuration
 * Specifies which routes should be processed by the middleware
 * Excludes static files, images, favicon, and public folder
 */
export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * 1. _next/static (static files)
     * 2. _next/image (image optimization files)
     * 3. favicon.ico (favicon file)
     * 4. public folder
     */
    '/((?!_next/static|_next/image|favicon.ico|public/).*)',
  ],
}; 