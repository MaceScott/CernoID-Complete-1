'use client';

import { ReactNode, createContext, useContext, useEffect, useState } from 'react';
import { wsService } from '../lib/websocket-service';
import { WebSocketState } from '../types/shared';

interface WebSocketContextType {
  state: WebSocketState;
  send: (message: any) => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export function useWebSocketContext() {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider');
  }
  return context;
}

interface WebSocketProviderProps {
  children: ReactNode;
}

export function WebSocketProvider({ children }: WebSocketProviderProps) {
  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    reconnectAttempts: 0,
  });

  useEffect(() => {
    const unsubscribe = wsService.onStateChange((newState) => {
      setState(newState);
    });

    return () => {
      unsubscribe();
      wsService.disconnect();
    };
  }, []);

  const contextValue: WebSocketContextType = {
    state,
    send: wsService.send,
  };

  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  );
} 