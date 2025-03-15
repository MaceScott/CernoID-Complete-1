import { NextRequest, NextResponse } from "next/server"
import { z } from "zod"
import { auth_service } from "../../../../core/security/security/auth"
import { DatabaseService } from "../../../../core/database/service"

// Get database service
const db = new DatabaseService()

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

    // Get user by email first
    const user = await db.get_user_by_email(email)
    if (!user) {
      return NextResponse.json(
        { error: "Invalid credentials" },
        { status: 401 }
      )
    }

    // Authenticate user with username and password
    const authenticated = await auth_service.authenticate_user(user.username, password)
    if (!authenticated) {
      return NextResponse.json(
        { error: "Invalid credentials" },
        { status: 401 }
      )
    }

    // Check if user is active
    if (!authenticated.is_active) {
      return NextResponse.json(
        { error: "Account is inactive" },
        { status: 403 }
      )
    }

    // Generate tokens
    const tokens = await auth_service.create_tokens(authenticated)

    // Return user data and tokens
    return NextResponse.json({
      user: {
        id: authenticated.id,
        email: authenticated.email,
        role: authenticated.role,
        permissions: authenticated.permissions,
        last_login: authenticated.last_login
      },
      ...tokens
    })

  } catch (error) {
    console.error('Login error:', error)
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}

// Handle GET requests with a proper error
export async function GET() {
  return NextResponse.json(
    { error: "Method not allowed" },
    { status: 405 }
  )
} 