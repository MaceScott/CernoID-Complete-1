import { NextRequest } from 'next/server';

export interface AuthConfig {
  publicRoutes: string[];
  tokenHeader: string;
  tokenPrefix: string;
}

export interface AuthContext {
  userId: string;
  role: string;
  permissions: string[];
}

export interface AuthMiddlewareOptions {
  config: AuthConfig;
  onError?: (error: Error) => void;
}

export type AuthMiddleware = (
  request: NextRequest,
  options: AuthMiddlewareOptions
) => Promise<Response | undefined>; 