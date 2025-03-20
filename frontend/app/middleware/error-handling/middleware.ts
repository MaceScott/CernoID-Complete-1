import { NextRequest, NextResponse } from 'next/server';
import { ErrorHandlingConfig, ErrorHandlingMiddlewareOptions } from './types';

export class ErrorHandlingMiddleware {
  private config: ErrorHandlingConfig;

  constructor(config: ErrorHandlingConfig) {
    this.config = config;
  }

  async handle(request: NextRequest, options: ErrorHandlingMiddlewareOptions): Promise<Response | undefined> {
    try {
      return NextResponse.next();
    } catch (error) {
      if (options.onError) {
        options.onError(error as Error);
      }

      if (this.config.logErrors) {
        console.error('Error in middleware:', error);
      }

      const errorResponse = this.handleError(error as Error);
      return this.createErrorResponse(errorResponse);
    }
  }

  private handleError(error: Error) {
    const errorName = error.constructor.name;
    const handler = this.config.handlers.get(errorName) || this.config.defaultHandler;
    return handler(error);
  }

  private createErrorResponse(errorResponse: { error: string; code?: string; details?: unknown }): Response {
    return new Response(JSON.stringify(errorResponse), {
      status: this.getStatusCode(errorResponse.code),
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  private getStatusCode(code?: string): number {
    switch (code) {
      case 'UNAUTHORIZED':
        return 401;
      case 'FORBIDDEN':
        return 403;
      case 'NOT_FOUND':
        return 404;
      case 'VALIDATION_ERROR':
        return 422;
      case 'RATE_LIMIT_EXCEEDED':
        return 429;
      case 'INTERNAL_ERROR':
      default:
        return 500;
    }
  }

  registerHandler(errorName: string, handler: (error: Error) => { error: string; code?: string; details?: unknown }): void {
    this.config.handlers.set(errorName, handler);
  }

  setDefaultHandler(handler: (error: Error) => { error: string; code?: string; details?: unknown }): void {
    this.config.defaultHandler = handler;
  }
} 