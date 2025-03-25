export interface AppSettings {
  theme: 'light' | 'dark';
  language: string;
  notifications: {
    enabled: boolean;
    sound: boolean;
    desktop: boolean;
  };
  security: {
    tokenExpiry: number;
    maxAttempts: number;
    lockoutDuration: number;
    require2fa: boolean;
    requireFacialRecognition: boolean;
    requirePassword: boolean;
    allowedAdminRoles: string[];
  };
  display: {
    density: 'compact' | 'comfortable' | 'spacious';
    fontSize: number;
    showThumbnails: boolean;
  };
  recognition: {
    confidenceThreshold: number;
    maxFaces: number;
    useGpu: boolean;
    modelType: string;
    detectLandmarks: boolean;
    extractDescriptor: boolean;
  };
  camera: {
    defaultDevice: string;
    resolution: string;
    fps: number;
    quality: number;
  };
  system: {
    autoStart: boolean;
    autoUpdate: boolean;
    logLevel: 'debug' | 'info' | 'warn' | 'error';
    retentionDays: number;
  };
}

export const DEFAULT_SETTINGS: AppSettings = {
  theme: 'light',
  language: 'en',
  notifications: {
    enabled: true,
    sound: true,
    desktop: true,
  },
  security: {
    tokenExpiry: 3600,
    maxAttempts: 5,
    lockoutDuration: 900,
    require2fa: false,
    requireFacialRecognition: false,
    requirePassword: true,
    allowedAdminRoles: ['admin', 'superadmin'],
  },
  display: {
    density: 'comfortable',
    fontSize: 14,
    showThumbnails: true,
  },
  recognition: {
    confidenceThreshold: 0.7,
    maxFaces: 1,
    useGpu: false,
    modelType: 'default',
    detectLandmarks: true,
    extractDescriptor: true,
  },
  camera: {
    defaultDevice: '',
    resolution: '1280x720',
    fps: 30,
    quality: 80,
  },
  system: {
    autoStart: false,
    autoUpdate: true,
    logLevel: 'info',
    retentionDays: 30,
  },
}; 