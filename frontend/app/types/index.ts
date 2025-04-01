// Re-export specific types from shared
export type {
  BaseEntity,
  PaginationParams,
  PaginatedResponse,
  ApiResponse,
  ErrorResponse,
  WebSocketMessage,
  WebSocketState,
  SystemMetrics,
  SystemStatus,
  AppConfig,
  CameraConfig
} from './shared';

// Re-export other types
export * from './auth';
export * from './features/settings';

// Theme type
export type Theme = 'light' | 'dark';

// User type
export interface User {
    id: string;
    username: string;
    email: string;
    name?: string;
    role: string;
    status: 'active' | 'inactive' | 'suspended';
    isAdmin: boolean;
    accessLevel: string;
    allowedZones: string[];
    lastLogin?: string;
    createdAt: string;
    updatedAt: string;
}

// Alert type
export interface Alert {
    id: string;
    type: string;
    severity: string;
    message: string;
    status: 'open' | 'resolved' | 'dismissed';
    cameraId?: string;
    camera?: {
        id: string;
        name: string;
        type: 'webcam' | 'ip' | 'facial' | 'security' | 'indoor' | 'outdoor';
        streamUrl: string;
        status: 'active' | 'inactive' | 'error';
        enabled: boolean;
        location?: string;
    };
    userId: string;
    user?: {
        id: string;
        name: string;
        email: string;
    };
    resolvedAt?: string;
    resolvedBy?: string;
    createdAt: string;
    updatedAt: string;
}

// Recognition types
export interface RecognitionResult {
    id: string;
    timestamp: string;
    faces: Face[];
    processing_time: number;
    image_info: {
        width: number;
        height: number;
        format: string;
    };
}

export interface Face {
    bbox: number[];
    confidence: number;
    landmarks?: number[][];
    features?: number[];
} 