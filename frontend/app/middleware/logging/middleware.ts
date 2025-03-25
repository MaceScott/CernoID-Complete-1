import { NextRequest, NextResponse } from 'next/server';
import { LogEntry, LoggingConfig, LoggingMiddlewareOptions } from './types';

export class LoggingMiddleware {
  private config: LoggingConfig;

  constructor(config: LoggingConfig) {
    this.config = config;
  }

  async handle(request: NextRequest, options: LoggingMiddlewareOptions): Promise<Response | undefined> {
    if (!this.config.enabled || this.shouldExcludePath(request.nextUrl.pathname)) {
      return NextResponse.next();
    }

    const startTime = Date.now();
    const requestId = this.generateRequestId();

    try {
      const response = await NextResponse.next();
      const duration = Date.now() - startTime;

      const logEntry: LogEntry = {
        timestamp: startTime,
        method: request.method,
        url: request.url,
        status: response.status,
        duration,
        ip: request.ip,
        userAgent: request.headers.get('user-agent') ?? undefined,
        requestId,
      };

      if (this.shouldLogPerformance(duration)) {
        this.logEntry(logEntry);
      }

      // Add request ID to response headers
      response.headers.set('X-Request-ID', requestId);
      return response;
    } catch (error) {
      const duration = Date.now() - startTime;
      const logEntry: LogEntry = {
        timestamp: startTime,
        method: request.method,
        url: request.url,
        status: 500,
        duration,
        ip: request.ip,
        userAgent: request.headers.get('user-agent') ?? undefined,
        requestId,
        error: error as Error,
      };

      if (this.config.logErrors) {
        this.logEntry(logEntry);
      }

      if (options.onError) {
        options.onError(error as Error);
      }

      throw error;
    }
  }

  private shouldExcludePath(path: string): boolean {
    if (!this.config.excludePaths) {
      return false;
    }
    return this.config.excludePaths.some(excludePath => path.startsWith(excludePath));
  }

  private shouldLogPerformance(duration: number): boolean {
    if (!this.config.logPerformance) {
      return false;
    }
    if (!this.config.performanceThreshold) {
      return true;
    }
    return duration >= this.config.performanceThreshold;
  }

  private generateRequestId(): string {
    return Math.random().toString(36).substring(2) + Date.now().toString(36);
  }

  private logEntry(entry: LogEntry): void {
    if (this.config.onLog) {
      this.config.onLog(entry);
    } else {
      console.log(JSON.stringify(entry));
    }
  }

  setConfig(config: Partial<LoggingConfig>): void {
    this.config = { ...this.config, ...config };
  }
} 