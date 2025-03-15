import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { verify } from 'jsonwebtoken';

// Routes that don't require authentication
const PUBLIC_ROUTES = ['/login', '/register', '/forgot-password'];

// Routes that require authentication
const PROTECTED_ROUTES = ['/dashboard', '/admin', '/settings', '/profile'];

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

  // Get session token from cookies
  const session = request.cookies.get('session');
  const isAuthenticated = !!session?.value;

  // Check if current route is public or protected
  const isPublicRoute = PUBLIC_ROUTES.some(route => pathname.startsWith(route));
  const isProtectedRoute = PROTECTED_ROUTES.some(route => pathname.startsWith(route));

  // Handle root path
  if (pathname === '/') {
    return NextResponse.redirect(
      new URL(isAuthenticated ? '/dashboard' : '/login', request.url)
    );
  }

  // Redirect authenticated users away from public routes
  if (isAuthenticated && isPublicRoute) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  // Redirect unauthenticated users to login
  if (!isAuthenticated && isProtectedRoute) {
    const response = NextResponse.redirect(new URL('/login', request.url));
    response.cookies.delete('session'); // Clear invalid session
    return response;
  }

  // Add user info to request headers for downstream handlers
  const response = NextResponse.next();
  if (isAuthenticated) {
    const payload = verify(session.value, JWT_SECRET) as {
      sub: string;
      email: string;
      role: string;
      permissions: string[];
    };
    response.headers.set('X-User-Role', payload.role);
  }

  return response;
}

// Configure which routes use this middleware
export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!_next/static|_next/image|favicon.ico|public/).*)',
  ],
}; 