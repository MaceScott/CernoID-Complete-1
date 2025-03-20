import { NextRequest } from 'next/server';

export interface ErrorResponse {
  error: string;
  code?: string;
  details?: unknown;
}

export interface ErrorHandler {
  (error: Error): ErrorResponse;
}

export interface ErrorHandlingConfig {
  handlers: Map<string, ErrorHandler>;
  defaultHandler: ErrorHandler;
  logErrors?: boolean;
}

export interface ErrorHandlingMiddlewareOptions {
  config: ErrorHandlingConfig;
  onError?: (error: Error) => void;
}

export type ErrorHandlingMiddleware = (
  request: NextRequest,
  options: ErrorHandlingMiddlewareOptions
) => Promise<Response | undefined>; 