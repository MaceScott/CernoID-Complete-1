import { useEffect, useRef, useState } from 'react';

type WebSocketMessage = {
  type: string;
  data: any;
};

export function useWebSocket(url?: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [messages, setMessages] = useState<string[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (typeof window === 'undefined' || !url) return;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      setError(null);
    };

    ws.onclose = () => {
      setIsConnected(false);
    };

    ws.onerror = (event) => {
      setError(new Error('WebSocket error occurred'));
      console.error('WebSocket error:', event);
    };

    ws.onmessage = (event) => {
      try {
        // Keep the raw message string as the component will parse it
        setMessages(prev => [...prev, event.data]);
      } catch (err) {
        console.error('Error handling WebSocket message:', err);
        setError(err instanceof Error ? err : new Error('Failed to handle WebSocket message'));
      }
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [url]);

  const sendMessage = (message: WebSocketMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  };

  return {
    isConnected,
    error,
    messages,
    sendMessage,
  };
}

export function useWebSocketMessage<T>(messageType: string) {
  const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
  const { messages } = useWebSocket(`${wsUrl}/ws/events`);
  const [lastMessage, setLastMessage] = useState<T | null>(null);

  useEffect(() => {
    if (!messages.length) return;
    
    const message = messages[messages.length - 1];
    try {
      const parsed = JSON.parse(message);
      if (parsed.type === messageType) {
        setLastMessage(parsed.data);
      }
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }, [messages, messageType]);

  return lastMessage;
} 