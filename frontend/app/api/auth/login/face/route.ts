import { NextResponse } from 'next/server';
import { z } from 'zod';
import { cookies } from 'next/headers';

const faceLoginSchema = z.object({
  faceData: z.string().min(1),
});

// Get origin from environment or default to localhost
const origin = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    
    // Validate request body
    const result = faceLoginSchema.safeParse(body);
    if (!result.success) {
      return NextResponse.json(
        { success: false, error: 'Invalid request data' },
        { 
          status: 400,
          headers: {
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Allow-Origin': origin,
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
          }
        }
      );
    }

    const { faceData } = result.data;

    // TODO: Implement actual face recognition
    // For now, we'll just check if the face data is valid base64
    try {
      // Check if the face data is valid base64
      const base64Regex = /^data:image\/[a-z]+;base64,/;
      if (!base64Regex.test(faceData)) {
        return NextResponse.json(
          { success: false, error: 'Invalid face data format' },
          { 
            status: 400,
            headers: {
              'Access-Control-Allow-Credentials': 'true',
              'Access-Control-Allow-Origin': origin,
              'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
              'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            }
          }
        );
      }

      // For testing purposes, always authenticate
      const sessionToken = Buffer.from(Date.now().toString()).toString('base64');
      
      const response = NextResponse.json({
        success: true,
        data: {
          user: {
            id: '1',
            email: 'admin@cernoid.com',
            name: 'Admin User',
            role: 'admin',
            permissions: ['admin'],
            zones: [],
          }
        }
      }, { 
        status: 200,
        headers: {
          'Access-Control-Allow-Credentials': 'true',
          'Access-Control-Allow-Origin': origin,
          'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        }
      });

      // Set session cookie with proper configuration
      response.cookies.set({
        name: 'session',
        value: sessionToken,
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        path: '/',
        maxAge: 60 * 60 * 24, // 24 hours
        domain: new URL(origin).hostname
      });

      return response;
    } catch (error) {
      console.error('Face data validation error:', error);
      return NextResponse.json(
        { success: false, error: 'Invalid face data' },
        { 
          status: 400,
          headers: {
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Allow-Origin': origin,
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
          }
        }
      );
    }
  } catch (error) {
    console.error('Face login error:', error);
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { 
        status: 500,
        headers: {
          'Access-Control-Allow-Credentials': 'true',
          'Access-Control-Allow-Origin': origin,
          'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        }
      }
    );
  }
}

// Handle OPTIONS request for CORS
export async function OPTIONS() {
  return NextResponse.json({}, {
    headers: {
      'Access-Control-Allow-Credentials': 'true',
      'Access-Control-Allow-Origin': origin,
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    }
  });
} 