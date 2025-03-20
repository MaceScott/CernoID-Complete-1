import { NextRequest, NextResponse } from 'next/server';
import { AuthConfig, AuthContext, AuthMiddlewareOptions } from './types';

export class AuthMiddleware {
  private config: AuthConfig;

  constructor(config: AuthConfig) {
    this.config = config;
  }

  async handle(request: NextRequest, options: AuthMiddlewareOptions): Promise<Response | undefined> {
    try {
      // Check if the route is public
      if (this.isPublicRoute(request.nextUrl.pathname)) {
        return NextResponse.next();
      }

      // Get token from header
      const token = this.getTokenFromHeader(request);
      if (!token) {
        return this.unauthorizedResponse();
      }

      // Validate token and get user context
      const context = await this.validateToken(token);
      if (!context) {
        return this.unauthorizedResponse();
      }

      // Add user context to request headers
      const requestHeaders = new Headers(request.headers);
      requestHeaders.set('x-user-id', context.userId);
      requestHeaders.set('x-user-role', context.role);
      requestHeaders.set('x-user-permissions', JSON.stringify(context.permissions));

      // Create new request with updated headers
      const newRequest = new NextRequest(request, {
        headers: requestHeaders,
      });

      return NextResponse.next({
        request: newRequest,
      });
    } catch (error) {
      if (options.onError) {
        options.onError(error as Error);
      }
      return this.errorResponse(error as Error);
    }
  }

  private isPublicRoute(pathname: string): boolean {
    return this.config.publicRoutes.some(route => pathname.startsWith(route));
  }

  private getTokenFromHeader(request: NextRequest): string | null {
    const authHeader = request.headers.get(this.config.tokenHeader);
    if (!authHeader) return null;

    if (!authHeader.startsWith(this.config.tokenPrefix)) {
      return null;
    }

    return authHeader.slice(this.config.tokenPrefix.length).trim();
  }

  private async validateToken(token: string): Promise<AuthContext | null> {
    try {
      // Implement token validation logic here
      // This would typically involve:
      // 1. Verifying token signature
      // 2. Checking token expiration
      // 3. Extracting user context
      return {
        userId: 'dummy-user-id',
        role: 'user',
        permissions: ['read']
      };
    } catch (error) {
      return null;
    }
  }

  private unauthorizedResponse(): Response {
    return new Response(JSON.stringify({ error: 'Unauthorized' }), {
      status: 401,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  private errorResponse(error: Error): Response {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }
} 