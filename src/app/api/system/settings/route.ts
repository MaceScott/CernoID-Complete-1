import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'

const settingsSchema = z.object({
  notifications: z.object({
    email: z.boolean(),
    push: z.boolean(),
    alerts: z.object({
      motion: z.boolean(),
      face: z.boolean(),
      system: z.boolean(),
    }),
  }),
  email: z.string().email(),
  retentionDays: z.number().min(1).max(365),
  cameraQuality: z.enum(['low', 'medium', 'high']),
})

export async function GET(request: NextRequest) {
  try {
    // TODO: Implement database query
    const settings = {
      notifications: {
        email: true,
        push: true,
        alerts: {
          motion: true,
          face: true,
          system: true,
        },
      },
      email: "admin@example.com",
      retentionDays: 30,
      cameraQuality: "high",
    }

    return NextResponse.json(settings)
  } catch (error) {
    console.error('Failed to fetch settings:', error)
    return NextResponse.json(
      { error: "Failed to fetch settings" },
      { status: 500 }
    )
  }
}

export async function PUT(request: NextRequest) {
  try {
    const body = await request.json()
    const result = settingsSchema.safeParse(body)

    if (!result.success) {
      return NextResponse.json(
        { error: "Invalid input", details: result.error.issues },
        { status: 400 }
      )
    }

    // TODO: Implement settings update in database
    const updatedSettings = {
      ...result.data,
      lastUpdated: new Date().toISOString(),
    }

    return NextResponse.json(updatedSettings)
  } catch (error) {
    console.error('Failed to update settings:', error)
    return NextResponse.json(
      { error: "Failed to update settings" },
      { status: 500 }
    )
  }
} 