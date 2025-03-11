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