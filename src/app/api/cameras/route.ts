import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'

const cameraSchema = z.object({
  name: z.string().min(1),
  location: z.string().min(1),
  type: z.enum(['indoor', 'outdoor']),
  resolution: z.string(),
  status: z.enum(['active', 'inactive']).default('active'),
})

export async function GET(request: NextRequest) {
  try {
    // TODO: Implement database query
    const cameras = [
      {
        id: "1",
        name: "Front Door",
        location: "Main Entrance",
        status: "active",
        type: "outdoor",
        resolution: "1080p",
        lastActive: new Date().toISOString()
      },
      {
        id: "2",
        name: "Reception",
        location: "Lobby",
        status: "active",
        type: "indoor",
        resolution: "4K",
        lastActive: new Date().toISOString()
      }
    ]

    // Filter by status if provided
    const { searchParams } = new URL(request.url)
    const status = searchParams.get('status')
    
    if (status) {
      return NextResponse.json(
        cameras.filter(camera => camera.status === status)
      )
    }

    return NextResponse.json(cameras)
  } catch (error) {
    console.error('Failed to fetch cameras:', error)
    return NextResponse.json(
      { error: "Failed to fetch cameras" },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const result = cameraSchema.safeParse(body)

    if (!result.success) {
      return NextResponse.json(
        { error: "Invalid input", details: result.error.issues },
        { status: 400 }
      )
    }

    // TODO: Implement camera creation in database
    const newCamera = {
      id: Math.random().toString(36).substr(2, 9),
      ...result.data,
      lastActive: new Date().toISOString()
    }

    return NextResponse.json(newCamera, { status: 201 })
  } catch (error) {
    console.error('Failed to create camera:', error)
    return NextResponse.json(
      { error: "Failed to create camera" },
      { status: 500 }
    )
  }
} 