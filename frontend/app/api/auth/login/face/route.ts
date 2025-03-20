/**
 * File: route.ts (face login)
 * Purpose: Implements facial recognition login endpoint.
 * 
 * Key Features:
 * - Face image data validation
 * - JWT token generation
 * - Secure cookie management
 * - CORS support
 * 
 * Dependencies:
 * - next/server: Next.js server utilities
 * - zod: Request validation
 * - jsonwebtoken: JWT token generation
 * - Environment variables:
 *   - JWT_SECRET: Secret key for JWT signing
 * 
 * Note: Current implementation is a demo that simulates face recognition.
 * In production, this should be replaced with a proper face recognition service.
 * 
 * Endpoints:
 * POST /api/auth/login/face
 * - Validates face image data
 * - Returns user data and sets session cookie
 * 
 * OPTIONS /api/auth/login/face
 * - Handles CORS preflight requests
 */

import { NextRequest } from 'next/server';
import { validateRequest } from '@/api/utils/validation';
import { checkRateLimit, rateLimits } from '@/api/utils/rate-limit';
import { logger } from '@/api/utils/logger';
import { createSessionToken, setSessionCookie, createSuccessResponse, createErrorResponse, createCorsResponse } from '@/api/utils/auth';
import { z } from 'zod';

// Face login request schema
const faceLoginSchema = z.object({
  imageData: z.string().min(1),
});

/**
 * POST /api/auth/login/face
 * Handles user authentication via facial recognition
 * 
 * @param request - HTTP request object containing face image data
 * @returns NextResponse with user data and session cookie, or error
 */
export async function POST(request: NextRequest) {
  try {
    // Log the request
    logger.logRequest(request, 'Face login attempt');

    // Check rate limit
    if (!(await checkRateLimit(request, rateLimits.auth.faceLogin))) {
      logger.warn('Rate limit exceeded for face login', { path: request.nextUrl.pathname });
      return createErrorResponse('Too many face login attempts. Please try again later.', 429);
    }

    // Validate request body
    const { imageData } = await validateRequest(request, faceLoginSchema);

    // TODO: Replace with actual face recognition
    // For now, simulate face recognition check
    const faceRecognized = true;
    if (!faceRecognized) {
      logger.warn('Face not recognized', { path: request.nextUrl.pathname });
      return createErrorResponse('Face not recognized', 401);
    }

    // TODO: Replace with actual user data from face recognition
    const user = {
      id: '123',
      email: 'test@example.com',
      name: 'Test User',
      role: 'user'
    };

    // Create session token
    const token = await createSessionToken(user);

    // Set session cookie
    const response = createSuccessResponse({ user });
    await setSessionCookie(response, token);

    logger.info('Face login successful', { userId: user.id });
    return response;
  } catch (error) {
    logger.logError(error as Error, request);
    
    if (error instanceof z.ZodError) {
      return createErrorResponse('Invalid face login request', 400);
    }

    return createErrorResponse('Face login failed', 500);
  }
}

/**
 * OPTIONS /api/auth/login/face
 * Handles CORS preflight requests with credentials support
 * 
 * @returns NextResponse with CORS headers
 */
export async function OPTIONS() {
  return createCorsResponse();
} 