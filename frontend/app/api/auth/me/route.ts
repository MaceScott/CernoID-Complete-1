import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';

// Get origin from environment or default to localhost
const origin = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';

export async function GET(request: Request) {
  try {
    // Get session cookie
    const cookieStore = cookies();
    const sessionCookie = cookieStore.get('session');

    if (!sessionCookie) {
      return NextResponse.json(
        { success: false, error: 'Not authenticated' },
        { 
          status: 401,
          headers: {
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Allow-Origin': origin,
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
          }
        }
      );
    }

    // For demo purposes, return a mock user
    // In a real app, you would validate the session token and fetch the user from a database
    return NextResponse.json(
      {
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
      },
      { 
        status: 200,
        headers: {
          'Access-Control-Allow-Credentials': 'true',
          'Access-Control-Allow-Origin': origin,
          'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        }
      }
    );
  } catch (error) {
    console.error('Auth check error:', error);
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