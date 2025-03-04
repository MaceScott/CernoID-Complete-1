export interface AppSettings {
    theme: 'light' | 'dark';
    language: string;
    notifications: {
        enabled: boolean;
        sound: boolean;
        desktop: boolean;
    };
    security: {
        autoLock: boolean;
        lockTimeout: number;
        requireMFA: boolean;
    };
    display: {
        density: 'compact' | 'comfortable' | 'spacious';
        fontSize: number;
        showThumbnails: boolean;
    };
    recognition: {
        minConfidence: number;
        enableFaceTracking: boolean;
        saveDetections: boolean;
    };
    system: {
        autoUpdate: boolean;
        logLevel: 'debug' | 'info' | 'warn' | 'error';
        retentionDays: number;
    };
} 