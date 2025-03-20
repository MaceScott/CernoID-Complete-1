export * from './types';
export * from './middleware';

import { AuthConfig } from './types';
import { AuthMiddleware } from './middleware';

const defaultConfig: AuthConfig = {
  publicRoutes: ['/api/auth', '/api/public'],
  tokenHeader: 'Authorization',
  tokenPrefix: 'Bearer ',
};

export const authMiddleware = new AuthMiddleware(defaultConfig); 