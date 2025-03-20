import { NextRequest, NextResponse } from 'next/server';
import { authMiddleware } from './middleware/auth';
import { rateLimitMiddleware } from './middleware/rate-limit';
import { errorHandlingMiddleware } from './middleware/error-handling';
import { loggingMiddleware } from './middleware/logging';

export async function middleware(request: NextRequest) {
  try {
    // Apply logging middleware first
    const loggingResponse = await loggingMiddleware.handle(request, {
      config: loggingMiddleware['config'],
      onError: (error) => {
        console.error('Logging middleware error:', error);
      },
    });

    if (loggingResponse) {
      return loggingResponse;
    }

    // Apply rate limiting
    const rateLimitResponse = await rateLimitMiddleware.handle(request, {
      config: rateLimitMiddleware['config'],
      onError: (error) => {
        console.error('Rate limit middleware error:', error);
      },
    });

    if (rateLimitResponse) {
      return rateLimitResponse;
    }

    // Apply authentication
    const authResponse = await authMiddleware.handle(request, {
      config: authMiddleware['config'],
      onError: (error) => {
        console.error('Auth middleware error:', error);
      },
    });

    if (authResponse) {
      return authResponse;
    }

    // Apply error handling
    const errorResponse = await errorHandlingMiddleware.handle(request, {
      config: errorHandlingMiddleware['config'],
      onError: (error) => {
        console.error('Error handling middleware error:', error);
      },
    });

    if (errorResponse) {
      return errorResponse;
    }

    return NextResponse.next();
  } catch (error) {
    console.error('Middleware error:', error);
    return new Response(JSON.stringify({ error: 'Internal Server Error' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
}; 