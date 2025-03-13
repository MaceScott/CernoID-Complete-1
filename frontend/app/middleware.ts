import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Get origin from environment or default to localhost
const origin = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';

export function middleware(request: NextRequest) {
  // Allow API routes to be accessed directly
  if (request.nextUrl.pathname.startsWith('/api/')) {
    const response = NextResponse.next();
    
    // Add CORS headers for API routes
    response.headers.set('Access-Control-Allow-Credentials', 'true');
    response.headers.set('Access-Control-Allow-Origin', origin);
    response.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    
    return response;
  }

  // Check for authentication on protected routes
  const isAuthenticated = request.cookies.has('session');
  
  // Protected routes that require authentication
  if (request.nextUrl.pathname.startsWith('/dashboard') && !isAuthenticated) {
    const response = NextResponse.redirect(new URL('/login', request.url));
    response.headers.set('Access-Control-Allow-Credentials', 'true');
    response.headers.set('Access-Control-Allow-Origin', origin);
    return response;
  }

  // Public routes
  if (request.nextUrl.pathname === '/login' && isAuthenticated) {
    const response = NextResponse.redirect(new URL('/dashboard', request.url));
    response.headers.set('Access-Control-Allow-Credentials', 'true');
    response.headers.set('Access-Control-Allow-Origin', origin);
    return response;
  }

  const response = NextResponse.next();
  response.headers.set('Access-Control-Allow-Credentials', 'true');
  response.headers.set('Access-Control-Allow-Origin', origin);
  return response;
}

export const config = {
  matcher: [
    '/dashboard/:path*',
    '/api/:path*',
    '/login',
    '/register',
    '/forgot-password'
  ]
}; 