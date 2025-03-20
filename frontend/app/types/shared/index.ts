// Base interfaces
export interface BaseEntity {
  id: string;
  createdAt: string;
  updatedAt: string;
}

export interface PaginationParams {
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface ErrorResponse {
  success: false;
  error: string;
  message?: string;
}

// WebSocket types
export interface WebSocketMessage {
  type: string;
  payload: any;
}

export interface WebSocketState {
  connected: boolean;
  connecting: boolean;
  error: string | null;
  lastMessage: WebSocketMessage | null;
}

// System types
export interface SystemMetrics {
  cpu: number;
  memory: number;
  disk: number;
  uptime: number;
}

export interface SystemStatus {
  uptime: number;
  activeUsers: number;
  cameras?: {
    [key: string]: {
      status: string;
      fps: number;
      facesDetected: number;
      lastAlert?: string;
    };
  };
  alerts?: {
    total: number;
    open: number;
    resolved: number;
    bySeverity: {
      low: number;
      medium: number;
      high: number;
    };
  };
  recognition?: {
    matcher: {
      accuracy: number;
      latency: number;
      throughput: number;
    };
    registration: {
      total: number;
      pending: number;
      failed: number;
    };
  };
  notifications?: {
    [channel: string]: {
      status: string;
      sent: number;
      failed: number;
      queue: number;
    };
  };
  performance?: {
    cpuUsage: number;
    memoryUsage: number;
    diskUsage: number;
    networkIo: {
      rxBytes: number;
      txBytes: number;
    };
  };
}

export interface AppConfig {
  apiUrl: string;
  wsUrl: string;
  environment: 'development' | 'production' | 'test';
} 