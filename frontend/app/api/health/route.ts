import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';
export const runtime = 'edge';

export async function GET() {
  try {
    // Check frontend health
    const frontendHealth = {
      status: 'healthy',
      timestamp: new Date().toISOString()
    };

    // Then check backend health with timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    const backendHealth = await fetch('http://backend:8000/health', {
      signal: controller.signal
    }).finally(() => clearTimeout(timeoutId));

    if (!backendHealth.ok) {
      return NextResponse.json({
        status: 'unhealthy',
        frontend: frontendHealth,
        backend: { error: 'Backend health check failed' }
      }, { status: 503 });
    }

    const backendData = await backendHealth.json();

    return NextResponse.json({
      status: 'healthy',
      frontend: frontendHealth,
      backend: backendData
    });
  } catch (error) {
    console.error('Health check failed:', error);
    return NextResponse.json({
      status: 'unhealthy',
      error: 'System is not healthy'
    }, { status: 503 });
  }
} 