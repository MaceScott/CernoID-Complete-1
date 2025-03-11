import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';
export const runtime = 'edge';

export async function GET() {
  try {
    // First check if our frontend is running
    const frontendStatus = { running: true };

    // Then check backend health with timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    try {
      const backendHealth = await fetch('http://backend:8000/api/health', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!backendHealth.ok) {
        return NextResponse.json(
          { 
            status: 'degraded',
            frontend: frontendStatus,
            backend: { error: 'Backend health check failed' }
          },
          { status: 200 }
        );
      }

      const backendData = await backendHealth.json();

      return NextResponse.json(
        { 
          status: 'healthy',
          frontend: frontendStatus,
          backend: backendData
        },
        { 
          status: 200,
          headers: {
            'Cache-Control': 'no-store, must-revalidate',
            'Pragma': 'no-cache'
          }
        }
      );
    } catch (backendError) {
      // If backend is not reachable, still return 200 but with degraded status
      return NextResponse.json(
        { 
          status: 'degraded',
          frontend: frontendStatus,
          backend: { error: 'Backend not reachable' }
        },
        { status: 200 }
      );
    }
  } catch (error) {
    console.error('Health check failed:', error);
    return NextResponse.json(
      { 
        status: 'unhealthy',
        error: 'System is not healthy',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 503 }
    );
  }
} 