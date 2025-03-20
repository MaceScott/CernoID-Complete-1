import { NextRequest } from 'next/server';
import { createErrorResponse } from './auth';

interface RateLimitConfig {
  windowMs: number;    // Time window in milliseconds
  maxRequests: number; // Maximum requests per window
}

const defaultConfig: RateLimitConfig = {
  windowMs: 60 * 1000, // 1 minute
  maxRequests: 30      // 30 requests per minute
};

const sensitiveConfig: RateLimitConfig = {
  windowMs: 15 * 60 * 1000, // 15 minutes
  maxRequests: 5            // 5 requests per 15 minutes
};

// In-memory store for rate limiting
// In production, use Redis or similar for distributed rate limiting
const rateLimit = new Map<string, { count: number; resetTime: number }>();

/**
 * Checks if a request should be rate limited
 * @param request NextRequest object
 * @param config Rate limit configuration
 * @returns true if request is allowed, false if rate limited
 */
export async function checkRateLimit(
  request: NextRequest,
  config: RateLimitConfig = defaultConfig
): Promise<boolean> {
  const key = getRequestKey(request);
  const now = Date.now();
  
  // Clean up expired entries
  cleanupExpiredEntries();

  const limit = rateLimit.get(key);
  if (!limit) {
    // First request
    rateLimit.set(key, {
      count: 1,
      resetTime: now + config.windowMs
    });
    return true;
  }

  if (now > limit.resetTime) {
    // Window expired, reset counter
    rateLimit.set(key, {
      count: 1,
      resetTime: now + config.windowMs
    });
    return true;
  }

  if (limit.count >= config.maxRequests) {
    // Rate limit exceeded
    return false;
  }

  // Increment counter
  limit.count++;
  return true;
}

/**
 * Gets a unique key for the request based on IP and path
 */
function getRequestKey(request: NextRequest): string {
  const ip = request.ip || request.headers.get('x-forwarded-for') || 'unknown';
  return `${ip}:${request.nextUrl.pathname}`;
}

/**
 * Cleans up expired rate limit entries
 */
function cleanupExpiredEntries(): void {
  const now = Date.now();
  Array.from(rateLimit.entries()).forEach(([key, value]) => {
    if (now > value.resetTime) {
      rateLimit.delete(key);
    }
  });
}

/**
 * Rate limit configurations for different endpoints
 */
export const rateLimits = {
  default: defaultConfig,
  sensitive: sensitiveConfig,
  auth: {
    login: sensitiveConfig,
    register: sensitiveConfig,
    faceLogin: sensitiveConfig,
  }
}; 