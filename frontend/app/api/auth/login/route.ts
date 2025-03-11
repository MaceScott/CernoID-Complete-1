import { NextResponse } from 'next/server';
import { z } from 'zod';
import { cookies } from 'next/headers';

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
});

export async function POST(request: Request) {
  try {
    console.log('Login request received');
    const body = await request.json();
    console.log('Request body:', body);
    
    // Validate request body
    const result = loginSchema.safeParse(body);
    if (!result.success) {
      console.log('Validation failed:', result.error);
      return NextResponse.json(
        { success: false, error: 'Invalid request data' },
        { status: 400 }
      );
    }

    const { email, password } = result.data;
    console.log('Attempting login for email:', email);

    // Check for default admin credentials
    if (email === 'admin@cernoid.com' && password === 'admin123') {
      console.log('Admin login successful');
      
      // Create response with user data
      const response = NextResponse.json({
        success: true,
        data: {
          user: {
            id: '1',
            email: 'admin@cernoid.com',
            role: 'admin',
            permissions: ['admin'],
            zones: [],
          }
        }
      }, { status: 200 });

      // Set session cookie
      response.cookies.set({
        name: 'session',
        value: 'authenticated',
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        maxAge: 60 * 60 * 24 // 24 hours
      });

      return response;
    }

    console.log('Invalid credentials for email:', email);
    // If not default admin, return error
    return NextResponse.json(
      { success: false, error: 'Invalid credentials' },
      { status: 401 }
    );

  } catch (error) {
    console.error('Login error:', error);
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    );
  }
} 