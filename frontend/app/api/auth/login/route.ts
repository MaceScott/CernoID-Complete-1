/**
 * File: route.ts (login)
 * Purpose: Implements the traditional email/password login endpoint.
 * 
 * Key Features:
 * - Request validation using zod
 * - JWT token generation and management
 * - Secure cookie management
 * - Rate limiting and security
 * - CORS support
 * 
 * Dependencies:
 * - next/server: Next.js server utilities
 * - zod: Request validation
 * - Environment variables:
 *   - BACKEND_URL: Backend API URL
 *   - NEXT_PUBLIC_APP_URL: Application URL for CORS
 */

import { NextRequest } from "next/server"
import { z } from "zod"
import { auth_service } from "@/core/security/security/auth"
import {
  createSessionToken,
  setSessionCookie,
  createSuccessResponse,
  createErrorResponse,
  createCorsResponse,
  UserData
} from "@/api/utils/auth"
import { validateRequest } from '@/api/utils/validation'
import { checkRateLimit, rateLimits } from '@/api/utils/rate-limit'
import { logger } from '@/api/utils/logger'

// Get environment variables
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || process.env.BACKEND_URL || 'http://localhost:8000';
const origin = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';

/**
 * Login request validation schema
 * Ensures email and password meet security requirements
 */
const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
})

/**
 * POST /api/auth/login
 * Handles user authentication via email/password
 * 
 * @param request - HTTP request object containing email and password
 * @returns NextResponse with user data and session cookie, or error
 */
export async function POST(request: NextRequest) {
  try {
    // Log the request
    logger.logRequest(request, 'Login attempt');

    // Check rate limit
    if (!(await checkRateLimit(request, rateLimits.auth.login))) {
      logger.warn('Rate limit exceeded for login', { path: request.nextUrl.pathname });
      return createErrorResponse('Too many login attempts. Please try again later.', 429);
    }

    // Validate request body
    const { email, password } = await validateRequest(request, loginSchema);

    // Authenticate user
    console.log('[Login API] Authenticating user');
    const authenticated = await auth_service.authenticate_user(email, password);
    if (!authenticated) {
      console.log('[Login API] Authentication failed');
      return createErrorResponse("Invalid credentials", 401);
    }

    // Check if user is active
    if (!authenticated.is_active) {
      console.log('[Login API] User account inactive');
      return createErrorResponse("Account is inactive", 403);
    }

    // Create user data object
    const userData: UserData = {
      id: authenticated.id,
      email: authenticated.email,
      username: authenticated.username,
      role: authenticated.role,
      permissions: authenticated.permissions,
      last_login: authenticated.last_login
    };

    // Generate token and set cookie
    console.log('[Login API] Generating token');
    const token = await createSessionToken(userData);
    const response = createSuccessResponse({ user: userData });
    await setSessionCookie(response, token);
    console.log('[Login API] Session cookie set');

    logger.info('Login successful', { userId: userData.id });
    return response;
  } catch (error) {
    logger.logError(error as Error, request);
    
    if (error instanceof z.ZodError) {
      return createErrorResponse('Invalid login credentials', 400);
    }

    return createErrorResponse('Login failed', 500);
  }
}

/**
 * GET /api/auth/login
 * Handles GET requests with a proper error
 * 
 * @returns NextResponse with error message
 */
export async function GET() {
  return createErrorResponse("Method not allowed", 405);
}

/**
 * OPTIONS /api/auth/login
 * Handles CORS preflight requests
 * 
 * @returns NextResponse with CORS headers
 */
export async function OPTIONS() {
  return createCorsResponse();
} 