'use client';

import { ReactNode, createContext, useContext, useEffect, useState } from 'react';
import { websocketService } from '../lib/websocket-service';
import { WebSocketState, WebSocketMessage } from '@/types';

interface WebSocketContextType {
  state: WebSocketState;
  send: (message: WebSocketMessage) => void;
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
    connected: false,
    connecting: false,
    error: null,
    lastMessage: null
  });

  useEffect(() => {
    websocketService.connect();

    const handleOpen = () => {
      setState(prev => ({ ...prev, connected: true, connecting: false, error: null }));
    };

    const handleClose = () => {
      setState(prev => ({ ...prev, connected: false, connecting: false }));
    };

    const handleError = (error: Event) => {
      setState(prev => ({ ...prev, error: 'Connection error', connecting: false }));
    };

    const handleMessage = (message: WebSocketMessage) => {
      setState(prev => ({ ...prev, lastMessage: message }));
    };

    websocketService.subscribe('message', handleMessage);

    return () => {
      websocketService.disconnect();
    };
  }, []);

  const contextValue: WebSocketContextType = {
    state,
    send: websocketService.send
  };

  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  );
} 