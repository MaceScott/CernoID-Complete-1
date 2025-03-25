import { NextRequest } from 'next/server';

export interface LogEntry {
  timestamp: number;
  method: string;
  url: string;
  status: number;
  duration: number;
  ip?: string;
  userAgent?: string;
  requestId?: string;
  error?: Error;
}

export interface LoggingConfig {
  enabled: boolean;
  excludePaths?: string[];
  logErrors?: boolean;
  logPerformance?: boolean;
  performanceThreshold?: number; // in milliseconds
  onLog?: (entry: LogEntry) => void;
}

export interface LoggingMiddlewareOptions {
  config: LoggingConfig;
  onError?: (error: Error) => void;
}

export type LoggingMiddlewareFunction = (
  request: NextRequest,
  options: LoggingMiddlewareOptions
) => Promise<Response | undefined>; 