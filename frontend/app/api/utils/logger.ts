import { NextRequest } from 'next/server';

export enum LogLevel {
  INFO = 'INFO',
  WARN = 'WARN',
  ERROR = 'ERROR',
  DEBUG = 'DEBUG'
}

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  data?: any;
  path?: string;
  method?: string;
  ip?: string;
}

/**
 * Logger class for handling API logs
 */
class Logger {
  private static instance: Logger;
  private isDevelopment: boolean;

  private constructor() {
    this.isDevelopment = process.env.NODE_ENV === 'development';
  }

  public static getInstance(): Logger {
    if (!Logger.instance) {
      Logger.instance = new Logger();
    }
    return Logger.instance;
  }

  /**
   * Log an info message
   */
  public info(message: string, data?: any): void {
    this.log(LogLevel.INFO, message, data);
  }

  /**
   * Log a warning message
   */
  public warn(message: string, data?: any): void {
    this.log(LogLevel.WARN, message, data);
  }

  /**
   * Log an error message
   */
  public error(message: string, data?: any): void {
    this.log(LogLevel.ERROR, message, data);
  }

  /**
   * Log a debug message (only in development)
   */
  public debug(message: string, data?: any): void {
    if (this.isDevelopment) {
      this.log(LogLevel.DEBUG, message, data);
    }
  }

  /**
   * Log an API request
   */
  public logRequest(request: NextRequest, message: string = 'API Request'): void {
    const data = {
      path: request.nextUrl.pathname,
      method: request.method,
      ip: request.ip || request.headers.get('x-forwarded-for') || 'unknown',
      userAgent: request.headers.get('user-agent'),
    };
    this.info(message, data);
  }

  /**
   * Log an API error
   */
  public logError(error: Error, request?: NextRequest): void {
    const data: any = {
      name: error.name,
      message: error.message,
      stack: this.isDevelopment ? error.stack : undefined,
    };

    if (request) {
      data.path = request.nextUrl.pathname;
      data.method = request.method;
      data.ip = request.ip || request.headers.get('x-forwarded-for') || 'unknown';
    }

    this.error('API Error', data);
  }

  private log(level: LogLevel, message: string, data?: any): void {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      data
    };

    // In development, log to console
    if (this.isDevelopment) {
      const color = this.getLogColor(level);
      console.log(
        `${color}[${entry.timestamp}] ${level}${this.resetColor}: ${message}`,
        data ? '\n' + JSON.stringify(data, null, 2) : ''
      );
    } else {
      // In production, you would typically:
      // 1. Write to a log file
      // 2. Send to a logging service (e.g., CloudWatch, Datadog)
      // 3. Store in a database
      // For now, we'll just use console.log as a placeholder
      console.log(JSON.stringify(entry));
    }
  }

  private getLogColor(level: LogLevel): string {
    switch (level) {
      case LogLevel.INFO:
        return '\x1b[32m'; // Green
      case LogLevel.WARN:
        return '\x1b[33m'; // Yellow
      case LogLevel.ERROR:
        return '\x1b[31m'; // Red
      case LogLevel.DEBUG:
        return '\x1b[36m'; // Cyan
      default:
        return '';
    }
  }

  private resetColor = '\x1b[0m';
}

// Export a singleton instance
export const logger = Logger.getInstance(); 