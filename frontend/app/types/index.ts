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

export interface Camera {
    id: string;
    name: string;
    type: string;
    location: string;
    status: 'active' | 'inactive' | 'maintenance';
    zoneId: string;
    zone?: {
        id: string;
        name: string;
        level: number;
    };
    settings?: Record<string, unknown>;
    alerts?: Alert[];
    createdAt: string;
    updatedAt: string;
}

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
        type: string;
        location: string;
        status: string;
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

export interface SystemStatus {
    uptime: number;
    active_users: number;
    cameras?: {
        [key: string]: {
            status: string;
            fps: number;
            faces_detected: number;
            last_alert?: string;
        };
    };
    alerts?: {
        total: number;
        open: number;
        resolved: number;
        by_severity: {
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
        cpu_usage: number;
        memory_usage: number;
        disk_usage: number;
        network_io: {
            rx_bytes: number;
            tx_bytes: number;
        };
    };
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

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    limit: number;
    pages: number;
}

export type Theme = 'light' | 'dark'; 