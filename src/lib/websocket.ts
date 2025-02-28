"use client";

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useMemo,
  ReactNode,
} from "react";

interface WebSocketMessage {
  type: "alert" | "camera_status" | "system_status";
  data: any;
}

interface WebSocketContextType {
  send: (message: string) => void;
  close: () => void;
  lastMessage: string | null;
  messages: string[];
  isConnected: boolean;
}

// ✅ Export the WebSocket Context
export const WebSocketContext = createContext<WebSocketContextType | null>(null);

interface WebSocketProviderProps {
  children: ReactNode;
  customUrl?: string;
}

export function WebSocketProvider({ children, customUrl }: WebSocketProviderProps) {
  const [wsClient, setWsClient] = useState<WebSocket | null>(null);
  const [lastMessage, setLastMessage] = useState<string | null>(null);
  const [messages, setMessages] = useState<string[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  useEffect(() => {
    const wsUrl = customUrl || process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:3001";

    let ws: WebSocket;
    let reconnectTimeout: NodeJS.Timeout;

    const connectWebSocket = () => {
      ws = new WebSocket(wsUrl);
      setWsClient(ws);

      ws.onopen = () => {
        console.log("WebSocket connected:", wsUrl);
        setIsConnected(true);
        setReconnectAttempts(0);
      };

      ws.onmessage = (event) => {
        if (typeof event.data === "string") {
          setLastMessage(event.data);
          setMessages((prev) => [...prev, event.data]);
        }
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        setIsConnected(false);
      };

      ws.onclose = () => {
        console.warn("WebSocket closed, attempting to reconnect...");
        setIsConnected(false);
        if (reconnectAttempts < 5) {
          reconnectTimeout = setTimeout(connectWebSocket, 3000);
          setReconnectAttempts((prev) => prev + 1);
        } else {
          console.error("Max WebSocket reconnect attempts reached.");
        }
      };
    };

    connectWebSocket();

    return () => {
      if (ws) {
        ws.close();
      }
      clearTimeout(reconnectTimeout);
    };
  }, [customUrl]);

  const wsValue = useMemo<WebSocketContextType>(
    () => ({
      send: (message: string) => wsClient?.send(message),
      close: () => wsClient?.close(),
      lastMessage,
      messages,
      isConnected,
    }),
    [wsClient, lastMessage, messages, isConnected]
  );

  return (
    <WebSocketContext.Provider value={wsValue}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocket() {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error("useWebSocket must be used within a WebSocketProvider");
  }
  return context;
}

export function useWebSocketMessage<T>(type: WebSocketMessage["type"]) {
  const { messages } = useWebSocket();
  const [message, setMessage] = useState<T | null>(null);

  useEffect(() => {
    const lastMsg = messages.find((msg) => {
      try {
        const parsed = JSON.parse(msg);
        return parsed.type === type;
      } catch {
        return false;
      }
    });

    if (lastMsg) {
      setMessage(JSON.parse(lastMsg).data);
    }
  }, [messages, type]);

  return message;
}

