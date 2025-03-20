export * from './types';
export * from './middleware';

import { RateLimitConfig } from './types';
import { RateLimitMiddleware } from './middleware';

const defaultConfig: RateLimitConfig = {
  maxRequests: 100,
  windowMs: 15 * 60 * 1000, // 15 minutes
};

export const rateLimitMiddleware = new RateLimitMiddleware(defaultConfig); 