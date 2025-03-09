import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // If the user is trying to access the root path, redirect to login
  if (request.nextUrl.pathname === '/') {
    return NextResponse.redirect(new URL('/login', request.url), {
      status: 308 // Permanent redirect
    });
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    // Only match the root path
    '/'
  ],
}; 