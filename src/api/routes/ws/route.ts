import { NextRequest, NextResponse } from 'next/server'
import { WebSocketServer } from 'ws'

// Note: This requires additional server setup as Next.js API routes
// don't directly support WebSocket. You might need to use a custom server.

const wss = new WebSocketServer({ noServer: true })

wss.on('connection', (ws) => {
  console.log('Client connected')

  ws.on('message', (message) => {
    try {
      const data = JSON.parse(message.toString())
      // Handle different message types
      switch (data.type) {
        case 'subscribe_camera':
          // Handle camera subscription
          break
        case 'subscribe_alerts':
          // Handle alerts subscription
          break
        default:
          console.warn('Unknown message type:', data.type)
      }
    } catch (error) {
      console.error('Failed to handle WebSocket message:', error)
    }
  })

  ws.on('close', () => {
    console.log('Client disconnected')
  })
})

// Broadcast to all connected clients
function broadcast(message: any) {
  wss.clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(JSON.stringify(message))
    }
  })
}

// This is a placeholder route handler as Next.js API routes don't support WebSocket directly
export async function GET(_request: NextRequest) {
  return new Response('WebSocket endpoint', {
    status: 426,
    statusText: 'Upgrade Required'
  });
} 