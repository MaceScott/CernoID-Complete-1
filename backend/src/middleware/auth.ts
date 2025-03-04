import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { jwtVerify } from 'jose'

const JWT_SECRET = new TextEncoder().encode(
  process.env.JWT_SECRET || 'default-secret-key'
)

export async function validateAuth(request: NextRequest) {
  try {
    const token = request.headers.get('Authorization')?.split(' ')[1]
    
    if (!token) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      )
    }

    const { payload } = await jwtVerify(token, JWT_SECRET)
    
    // Add user info to request headers for downstream handlers
    const headers = new Headers(request.headers)
    headers.set('X-User-Id', payload.sub as string)
    headers.set('X-User-Role', payload.role as string)

    return NextResponse.next({
      request: {
        headers
      }
    })
  } catch (error) {
    console.error('Auth validation error:', error)
    return NextResponse.json(
      { error: 'Invalid token' },
      { status: 401 }
    )
  }
} 