import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'

const alertSchema = z.object({
  type: z.enum(['motion', 'face', 'system', 'error']),
  message: z.string(),
  priority: z.enum(['low', 'medium', 'high']),
  cameraId: z.string().optional(),
})

export async function GET(request: NextRequest) {
  try {
    // TODO: Implement database query
    const alerts = [
      {
        id: "1",
        type: "motion",
        message: "Motion detected in restricted area",
        timestamp: new Date().toISOString(),
        status: "new",
        priority: "high",
        cameraId: "cam-1"
      },
      // Add more mock alerts
    ]

    // Parse URL search params for filtering
    const { searchParams } = new URL(request.url)
    const status = searchParams.get('status')
    const type = searchParams.get('type')

    let filteredAlerts = alerts
    if (status) {
      filteredAlerts = filteredAlerts.filter(alert => alert.status === status)
    }
    if (type) {
      filteredAlerts = filteredAlerts.filter(alert => alert.type === type)
    }

    return NextResponse.json(filteredAlerts)
  } catch (error) {
    console.error('Failed to fetch alerts:', error)
    return NextResponse.json(
      { error: "Failed to fetch alerts" },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const result = alertSchema.safeParse(body)

    if (!result.success) {
      return NextResponse.json(
        { error: "Invalid input", details: result.error.issues },
        { status: 400 }
      )
    }

    // TODO: Implement alert creation in database
    const newAlert = {
      id: Math.random().toString(36).substr(2, 9),
      ...result.data,
      timestamp: new Date().toISOString(),
      status: "new",
    }

    return NextResponse.json(newAlert, { status: 201 })
  } catch (error) {
    console.error('Failed to create alert:', error)
    return NextResponse.json(
      { error: "Failed to create alert" },
      { status: 500 }
    )
  }
} 