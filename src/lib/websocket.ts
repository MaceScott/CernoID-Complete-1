'use client';

import React, { createContext, useContext, useEffect, useState, useMemo, Fragment } from 'react'
import { WebSocket } from 'ws'

interface WebSocketMessage {
  type: 'alert' | 'camera_status' | 'system_status'
  data: any
}

interface WebSocketContextType {
  send: (message: string) => void;
  close: () => void;
  lastMessage: string | null;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

let wsClient: WebSocket | null = null;

if (typeof window !== 'undefined') {
  wsClient = new WebSocket(process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:5000/ws');
}

export function useWebSocket() {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
}

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const [lastMessage, setLastMessage] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!wsClient) return;

    wsClient.onmessage = (event) => {
      setLastMessage(event.data);
    };

    return () => {
      wsClient?.close();
    };
  }, []);

  const wsValue = useMemo(() => {
    if (!wsClient) return null;
    
    return {
      send: (message: string) => wsClient?.send(message),
      close: () => wsClient?.close(),
      lastMessage
    };
  }, [lastMessage]);

  if (!wsValue) {
    return <>{children}</>;
  }

  return (
    <WebSocketContext.Provider value={wsValue}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocketMessage<T>(type: WebSocketMessage['type']) {
  const ws = useWebSocket()
  const [message, setMessage] = useState<T | null>(null)

  useEffect(() => {
    const unsubscribe = ws.subscribe((msg) => {
      if (msg.type === type) {
        setMessage(msg.data)
      }
    })
    return unsubscribe
  }, [ws, type])

  return message
} 
} 