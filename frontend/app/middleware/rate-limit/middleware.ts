import { NextRequest, NextResponse } from 'next/server';
import { RateLimitConfig, RateLimitInfo, RateLimitMiddlewareOptions } from './types';

export class RateLimitMiddleware {
  private config: RateLimitConfig;
  private requestCounts: Map<string, number> = new Map();
  private resetTimes: Map<string, number> = new Map();

  constructor(config: RateLimitConfig) {
    this.config = config;
  }

  async handle(request: NextRequest, options: RateLimitMiddlewareOptions): Promise<Response | undefined> {
    try {
      const key = this.getKey(request);
      const now = Date.now();
      const resetTime = this.resetTimes.get(key) || 0;

      // Reset if window has passed
      if (now >= resetTime) {
        this.requestCounts.set(key, 0);
        this.resetTimes.set(key, now + this.config.windowMs);
      }

      const count = this.requestCounts.get(key) || 0;
      const remaining = Math.max(0, this.config.maxRequests - count);

      // Check if rate limit exceeded
      if (remaining === 0) {
        return this.rateLimitExceededResponse(resetTime);
      }

      // Increment count
      this.requestCounts.set(key, count + 1);

      // Add rate limit info to response headers
      const response = NextResponse.next();
      response.headers.set('X-RateLimit-Limit', this.config.maxRequests.toString());
      response.headers.set('X-RateLimit-Remaining', remaining.toString());
      response.headers.set('X-RateLimit-Reset', resetTime.toString());

      return response;
    } catch (error) {
      if (options.onError) {
        options.onError(error as Error);
      }
      return this.errorResponse(error as Error);
    }
  }

  private getKey(request: NextRequest): string {
    if (this.config.keyGenerator) {
      return this.config.keyGenerator(request);
    }

    // Default key generator using IP address
    const ip = request.ip ?? 'unknown';
    return `${ip}:${request.nextUrl.pathname}`;
  }

  private rateLimitExceededResponse(resetTime: number): Response {
    return new Response(
      JSON.stringify({
        error: 'Too Many Requests',
        retryAfter: Math.ceil((resetTime - Date.now()) / 1000),
      }),
      {
        status: 429,
        headers: {
          'Content-Type': 'application/json',
          'Retry-After': Math.ceil((resetTime - Date.now()) / 1000).toString(),
        },
      }
    );
  }

  private errorResponse(error: Error): Response {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  getRateLimitInfo(key: string): RateLimitInfo {
    const now = Date.now();
    const resetTime = this.resetTimes.get(key) || 0;
    const count = this.requestCounts.get(key) || 0;
    const remaining = Math.max(0, this.config.maxRequests - count);

    return {
      remaining,
      resetTime,
      total: this.config.maxRequests,
    };
  }

  reset(key: string): void {
    this.requestCounts.delete(key);
    this.resetTimes.delete(key);
  }

  clear(): void {
    this.requestCounts.clear();
    this.resetTimes.clear();
  }
} 