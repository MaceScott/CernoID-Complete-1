import { NextRequest, NextResponse } from "next/server"
import { z } from "zod"

// Validation schema
const loginSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
})

// Export named functions for each HTTP method we want to support
export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    
    // Validate request body
    const result = loginSchema.safeParse(body)
    if (!result.success) {
      return NextResponse.json(
        { error: "Invalid input", details: result.error.issues },
        { status: 400 }
      )
    }

    const { email, password } = result.data

    // Log attempt (safely)
    console.log('Login attempt:', { email, timestamp: new Date().toISOString() })

    // Mock authentication - replace with real auth
    if (email === "macescott@gmail.com" && password === "Chronos#02") {
      return NextResponse.json({
        user: {
          id: "1",
          name: "Mace Scott",
          email: email,
          role: "admin",
          createdAt: new Date().toISOString(),
          lastLogin: new Date().toISOString(),
          status: "active"
        },
        token: "mock-jwt-token"
      })
    }

    return NextResponse.json(
      { error: "Invalid credentials" },
      { status: 401 }
    )
  } catch (error) {
    console.error('Login error:', error)
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}

// Optionally, handle GET requests with a proper error
export async function GET() {
  return NextResponse.json(
    { error: "Method not allowed" },
    { status: 405 }
  )
} 