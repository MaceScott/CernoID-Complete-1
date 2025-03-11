import { NextResponse } from 'next/server';
import { ZodError } from 'zod';
import { logger } from './logger';

export class AppError extends Error {
  constructor(
    message: string,
    public statusCode: number = 500,
    public code?: string
  ) {
    super(message);
    this.name = 'AppError';
  }
}

export const handleApiError = (error: unknown) => {
  if (error instanceof AppError) {
    logger.error(`AppError: ${error.message}`, { 
      code: error.code,
      statusCode: error.statusCode 
    });
    return NextResponse.json(
      { error: error.message, code: error.code },
      { status: error.statusCode }
    );
  }

  if (error instanceof ZodError) {
    logger.error('Validation Error', { issues: error.issues });
    return NextResponse.json(
      { 
        error: 'Validation Error',
        details: error.issues.map(issue => ({
          path: issue.path,
          message: issue.message
        }))
      },
      { status: 400 }
    );
  }

  logger.error('Unhandled Error', { error });
  return NextResponse.json(
    { error: 'Internal Server Error' },
    { status: 500 }
  );
}; 