export interface User {
    id: number;
    username: string;
    email: string;
    role: string;
    permissions: string[];
    is_active: boolean;
    last_login?: string;
    created_at: string;
}

export interface AppSettings {
    recognition: {
        min_confidence: number;
        max_faces: number;
        use_gpu: boolean;
        model_type: string;
    };
    security: {
        token_expiry: number;
        max_attempts: number;
        lockout_duration: number;
        require_2fa: boolean;
    };
    performance: {
        batch_size: number;
        cache_enabled: boolean;
        cache_size: number;
        worker_threads: number;
    };
    monitoring: {
        metrics_enabled: boolean;
        log_level: string;
        retention_days: number;
        alert_threshold: number;
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