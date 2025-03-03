import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Define protected routes and their required roles
const protectedRoutes = {
  '/admin': ['admin'],
  '/admin/users': ['admin'],
  '/admin/cameras': ['admin'],
  '/settings': ['admin', 'user'],
  '/review': ['admin', 'user'],
  '/alerts': ['admin', 'user'],
}

export async function middleware(request: NextRequest) {
  const token = request.cookies.get('authToken')
  const { pathname } = request.nextUrl

  console.log('Middleware - Path:', pathname, 'Token:', token ? 'exists' : 'none')

  // Public routes
  if (pathname.startsWith('/_next') || 
      pathname.startsWith('/api/auth') ||
      pathname.startsWith('/login')) {
    return NextResponse.next()
  }

  // No token, redirect to login
  if (!token) {
    console.log('Middleware - No token, redirecting to login')
    return NextResponse.redirect(new URL('/login', request.url))
  }

  // Verify token and get user role
  try {
    // TODO: Implement proper token verification
    const userRole = 'admin' // This should come from token verification

    // Check role-based access
    const requiredRoles = protectedRoutes[pathname as keyof typeof protectedRoutes]
    if (requiredRoles && !requiredRoles.includes(userRole)) {
      console.log('Middleware - Unauthorized access attempt')
      return NextResponse.redirect(new URL('/', request.url))
    }

    return NextResponse.next()
  } catch (error) {
    console.error('Middleware - Token verification failed:', error)
    return NextResponse.redirect(new URL('/login', request.url))
  }
}

// Configure which paths the middleware should run on
export const config = {
  matcher: ['/((?!api/auth|_next/static|_next/image|favicon.ico).*)'],
} 