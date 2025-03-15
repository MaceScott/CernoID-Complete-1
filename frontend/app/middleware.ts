import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { verify } from 'jsonwebtoken';

// Define protected and public routes
const protectedRoutes = [
  '/dashboard',
  '/profile',
  '/settings',
  '/users',
  '/logs',
  '/cameras',
];

const publicRoutes = [
  '/login',
  '/register',
  '/forgot-password',
  '/reset-password',
];

const JWT_SECRET = process.env.JWT_SECRET || 'default-secret-key';

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow API routes to be accessed directly
  if (pathname.startsWith('/api/')) {
    const response = NextResponse.next();
    // Add CORS headers for API routes
    response.headers.set('Access-Control-Allow-Origin', process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000');
    response.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    response.headers.set('Access-Control-Allow-Credentials', 'true');
    return response;
  }

  // Get session cookie
  const sessionCookie = request.cookies.get('session');
  let isAuthenticated = false;
  let userRole = '';

  if (sessionCookie) {
    try {
      // Verify JWT token
      const payload = verify(sessionCookie.value, JWT_SECRET) as {
        sub: string;
        email: string;
        role: string;
        permissions: string[];
      };
      isAuthenticated = true;
      userRole = payload.role;
    } catch (error) {
      console.error('Token validation error:', error);
      // Invalid token, clear it
      const response = NextResponse.redirect(new URL('/login', request.url));
      response.cookies.delete('session');
      return response;
    }
  }

  // Check for authentication on protected routes
  const isProtectedRoute = protectedRoutes.some(route => pathname.startsWith(route));
  const isPublicRoute = publicRoutes.some(route => pathname.startsWith(route));

  if (isProtectedRoute && !isAuthenticated) {
    const response = NextResponse.redirect(new URL('/login', request.url));
    response.cookies.delete('session');
    return response;
  }

  // Redirect authenticated users away from public routes
  if (isPublicRoute && isAuthenticated) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  // Redirect root to login if not authenticated, dashboard if authenticated
  if (pathname === '/') {
    return NextResponse.redirect(
      new URL(isAuthenticated ? '/dashboard' : '/login', request.url)
    );
  }

  // Add user info to request headers for downstream handlers
  const response = NextResponse.next();
  if (isAuthenticated) {
    response.headers.set('X-User-Role', userRole);
  }

  return response;
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
}; 