import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'

const userSchema = z.object({
  name: z.string().min(2),
  email: z.string().email(),
  role: z.enum(['admin', 'user']),
  status: z.enum(['active', 'inactive']).default('active'),
})

export async function GET(_request: Request) {
  try {
    // TODO: Implement database query
    const users = [
      {
        id: "1",
        name: "Mace Scott",
        email: "macescott@gmail.com",
        role: "admin",
        status: "active",
        createdAt: new Date().toISOString(),
        lastLogin: new Date().toISOString(),
      },
      // Add more mock users
    ]

    return NextResponse.json(users)
  } catch (error) {
    console.error('Failed to fetch users:', error)
    return NextResponse.json(
      { error: "Failed to fetch users" },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const result = userSchema.safeParse(body)

    if (!result.success) {
      return NextResponse.json(
        { error: "Invalid input", details: result.error.issues },
        { status: 400 }
      )
    }

    // TODO: Implement user creation in database
    const newUser = {
      id: Math.random().toString(36).substr(2, 9),
      ...result.data,
      createdAt: new Date().toISOString(),
      lastLogin: null,
    }

    return NextResponse.json(newUser, { status: 201 })
  } catch (error) {
    console.error('Failed to create user:', error)
    return NextResponse.json(
      { error: "Failed to create user" },
      { status: 500 }
    )
  }
} 