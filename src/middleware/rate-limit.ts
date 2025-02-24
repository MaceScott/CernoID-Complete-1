import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { Redis } from '@upstash/redis'

// Initialize Redis client
const redis = new Redis({
  url: process.env.UPSTASH_REDIS_REST_URL || '',
  token: process.env.UPSTASH_REDIS_REST_TOKEN || '',
})

// Rate limit configuration
const RATE_LIMIT_WINDOW = 60 // 1 minute
const MAX_REQUESTS = 100 // requests per window

export async function rateLimit(request: NextRequest) {
  const ip = request.ip || 'anonymous'
  const key = `rate-limit:${ip}`

  try {
    const requests = await redis.incr(key)
    
    if (requests === 1) {
      await redis.expire(key, RATE_LIMIT_WINDOW)
    }

    if (requests > MAX_REQUESTS) {
      return NextResponse.json(
        { error: 'Too many requests' },
        { status: 429 }
      )
    }

    // Add rate limit headers
    const response = NextResponse.next()
    response.headers.set('X-RateLimit-Limit', MAX_REQUESTS.toString())
    response.headers.set('X-RateLimit-Remaining', (MAX_REQUESTS - requests).toString())
    
    return response
  } catch (error) {
    console.error('Rate limiting error:', error)
    // Fall through to allow request if rate limiting fails
    return NextResponse.next()
  }
} 