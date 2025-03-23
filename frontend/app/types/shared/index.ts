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

export interface CameraConfig {
  id: string;
  name: string;
  type: 'webcam' | 'ip' | 'facial' | 'security' | 'indoor' | 'outdoor';
  url?: string;
  streamUrl: string;
  status: 'active' | 'inactive' | 'error';
  enabled: boolean;
  location?: string;
  zoneId?: string;
  zone?: {
    id: string;
    name: string;
    level: number;
  };
  settings?: {
    resolution?: string;
    fps?: number;
    quality?: number;
    recording?: boolean;
  };
  alerts?: Array<{
    id: string;
    type: string;
    severity: 'low' | 'medium' | 'high';
    message: string;
    status: 'open' | 'resolved' | 'dismissed';
    resolvedAt?: string;
    resolvedBy?: string;
  }>;
  createdAt?: string;
  updatedAt?: string;
}

export interface AppSettings {
    theme: 'light' | 'dark';
    language: string;
    notifications: {
        enabled: boolean;
        sound: boolean;
        desktop: boolean;
    };
    security: {
        token_expiry: number;
        max_attempts: number;
        lockout_duration: number;
        require_2fa: boolean;
        require_facial_recognition: boolean;
        require_password: boolean;
        allowed_admin_roles: string[];
    };
    display: {
        density: 'compact' | 'comfortable' | 'spacious';
        fontSize: number;
        showThumbnails: boolean;
    };
    recognition: {
        min_confidence: number;
        max_faces: number;
        use_gpu: boolean;
        model_type: string;
    };
    system: {
        autoUpdate: boolean;
        logLevel: 'debug' | 'info' | 'warn' | 'error';
        retentionDays: number;
    };
} 