export class AppError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number,
    public metadata?: Record<string, any>
  ) {
    super(message)
    this.name = 'AppError'
  }
}

export const errorCodes = {
  UNAUTHORIZED: 'UNAUTHORIZED',
  FORBIDDEN: 'FORBIDDEN',
  NOT_FOUND: 'NOT_FOUND',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  INTERNAL_ERROR: 'INTERNAL_ERROR',
} as const

export function handleApiError(error: unknown) {
  if (error instanceof AppError) {
    return {
      code: error.code,
      message: error.message,
      statusCode: error.statusCode,
      metadata: error.metadata,
    }
  }

  console.error('Unhandled error:', error)
  return {
    code: errorCodes.INTERNAL_ERROR,
    message: 'An unexpected error occurred',
    statusCode: 500,
  }
} 