export * from './types';
export * from './middleware';

import { LoggingConfig } from './types';
import { LoggingMiddleware } from './middleware';

const defaultConfig: LoggingConfig = {
  enabled: true,
  excludePaths: ['/api/health', '/api/metrics'],
  logErrors: true,
  logPerformance: true,
  performanceThreshold: 1000, // 1 second
};

export const loggingMiddleware = new LoggingMiddleware(defaultConfig); 