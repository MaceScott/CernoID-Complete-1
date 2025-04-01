import { useEffect, useRef, useState } from 'react';
import { WebSocketMessage } from '@/types/shared';

interface WebSocketHookOptions {
  url?: string;
  onMessage?: (data: WebSocketMessage) => void;
  onError?: (error: Event) => void;
  onClose?: (event: CloseEvent) => void;
  onOpen?: (event: Event) => void;
  reconnectAttempts?: number;
  reconnectInterval?: number;
}

export function useWebSocket({
  url = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws',
  onMessage,
  onError,
  onClose,
  onOpen,
  reconnectAttempts = 5,
  reconnectInterval = 3000,
}: WebSocketHookOptions = {}) {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Event | null>(null);
  const [messages, setMessages] = useState<string[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);

  useEffect(() => {
    const connect = () => {
      try {
        const ws = new WebSocket(url);

        ws.onopen = (event) => {
          setIsConnected(true);
          setError(null);
          reconnectCountRef.current = 0;
          onOpen?.(event);
        };

        ws.onmessage = (event) => {
          setMessages(prev => [...prev, event.data]);
          try {
            const data = JSON.parse(event.data);
            onMessage?.(data);
          } catch (err) {
            onMessage?.({ type: 'raw', payload: event.data });
          }
        };

        ws.onerror = (event) => {
          setError(event);
          onError?.(event);
        };

        ws.onclose = (event) => {
          setIsConnected(false);
          onClose?.(event);

          if (reconnectCountRef.current < reconnectAttempts) {
            setTimeout(() => {
              reconnectCountRef.current += 1;
              connect();
            }, reconnectInterval);
          }
        };

        wsRef.current = ws;
      } catch (err) {
        setError(err as Event);
        onError?.(err as Event);
      }
    };

    connect();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [url, onMessage, onError, onClose, onOpen, reconnectAttempts, reconnectInterval]);

  const send = (data: unknown) => {
    if (wsRef.current && isConnected) {
      wsRef.current.send(typeof data === 'string' ? data : JSON.stringify(data));
    }
  };

  return {
    isConnected,
    error,
    send,
    messages,
  };
}

export function useWebSocketMessage<T>(messageType: string, url = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws') {
  const [lastMessage, setLastMessage] = useState<T | null>(null);
  const { isConnected } = useWebSocket({
    url,
    onMessage: (data) => {
      if (data.type === messageType) {
        setLastMessage(data.payload as T);
      }
    },
  });

  return lastMessage;
} 