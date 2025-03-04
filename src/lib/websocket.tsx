import { useEffect, useRef, useState, createContext, useContext } from 'react';

interface WebSocketMessage {
  type: string;
  data: unknown;
}

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
  url = 'ws://localhost:8000/ws',
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
            onMessage?.({ type: 'raw', data: event.data });
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

export function useWebSocketMessage<T>(messageType: string, url = 'ws://localhost:8000/ws') {
  const [lastMessage, setLastMessage] = useState<T | null>(null);
  const { isConnected } = useWebSocket({
    url,
    onMessage: (data) => {
      if (data.type === messageType) {
        setLastMessage(data.data as T);
      }
    },
  });

  return lastMessage;
}

interface WebSocketContextType {
  isConnected: boolean;
  error: Event | null;
  send: (data: unknown) => void;
  messages: string[];
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const ws = useWebSocket();

  return (
    <WebSocketContext.Provider value={ws}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocketContext() {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider');
  }
  return context;
} 