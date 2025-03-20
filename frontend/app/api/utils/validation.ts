import { z } from 'zod';
import { createErrorResponse } from './auth';
import { NextRequest } from 'next/server';

/**
 * Validates request body against a Zod schema
 * @param request NextRequest object
 * @param schema Zod schema to validate against
 * @returns Parsed data if valid, throws error if invalid
 */
export async function validateRequest<T>(
  request: NextRequest,
  schema: z.Schema<T>
): Promise<T> {
  try {
    const body = await request.json();
    return schema.parse(body);
  } catch (error) {
    if (error instanceof z.ZodError) {
      throw new ValidationError('Invalid request data', error.issues);
    }
    throw new ValidationError('Failed to parse request body');
  }
}

/**
 * Custom error class for validation errors
 */
export class ValidationError extends Error {
  constructor(
    message: string,
    public details?: z.ZodIssue[]
  ) {
    super(message);
    this.name = 'ValidationError';
  }
}

/**
 * Common validation schemas
 */
export const schemas = {
  login: z.object({
    email: z.string().email('Invalid email address'),
    password: z.string().min(8, 'Password must be at least 8 characters'),
  }),

  faceLogin: z.object({
    imageData: z.string().min(1, 'Image data is required'),
  }),

  register: z.object({
    email: z.string().email('Invalid email address'),
    password: z.string().min(8, 'Password must be at least 8 characters'),
    name: z.string().min(2, 'Name must be at least 2 characters'),
    confirmPassword: z.string(),
  }).refine(data => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  }),
}; 