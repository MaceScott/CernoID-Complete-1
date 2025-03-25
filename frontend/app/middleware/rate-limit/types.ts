import { NextRequest } from 'next/server';

export interface RateLimitConfig {
  maxRequests: number;
  windowMs: number;
  keyGenerator?: (request: NextRequest) => string;
}

export interface RateLimitInfo {
  remaining: number;
  resetTime: number;
  total: number;
}

export interface RateLimitMiddlewareOptions {
  config: RateLimitConfig;
  onError?: (error: Error) => void;
}

export type RateLimitMiddlewareFunction = (
  request: NextRequest,
  options: RateLimitMiddlewareOptions
) => Promise<Response | undefined>; 