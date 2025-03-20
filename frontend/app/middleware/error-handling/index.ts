export * from './types';
export * from './middleware';

import { ErrorHandlingConfig } from './types';
import { ErrorHandlingMiddleware } from './middleware';

const defaultConfig: ErrorHandlingConfig = {
  handlers: new Map(),
  defaultHandler: (error: Error) => ({
    error: error.message,
    code: 'INTERNAL_ERROR',
    details: process.env.NODE_ENV === 'development' ? error.stack : undefined,
  }),
  logErrors: true,
};

export const errorHandlingMiddleware = new ErrorHandlingMiddleware(defaultConfig); 