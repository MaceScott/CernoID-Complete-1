import { NextRequest, NextResponse } from 'next/server'

export async function GET(_request: Request) {
  try {
    // TODO: Implement actual system monitoring
    const status = {
      cpu: Math.floor(Math.random() * 100),
      memory: Math.floor(Math.random() * 100),
      storage: Math.floor(Math.random() * 100),
      uptime: "5 days, 12 hours",
      lastUpdate: new Date().toISOString(),
      services: [
        {
          name: "Authentication",
          status: "operational",
          lastCheck: new Date().toISOString()
        },
        {
          name: "Camera Streams",
          status: "operational",
          lastCheck: new Date().toISOString()
        },
        {
          name: "Face Recognition",
          status: "degraded",
          lastCheck: new Date().toISOString()
        },
        {
          name: "Motion Detection",
          status: "operational",
          lastCheck: new Date().toISOString()
        }
      ]
    }

    return NextResponse.json(status)
  } catch (error) {
    console.error('Failed to fetch system status:', error)
    return NextResponse.json(
      { error: "Failed to fetch system status" },
      { status: 500 }
    )
  }
} 