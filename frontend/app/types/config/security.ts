export interface SecurityConfig {
  token: {
    expiry: number;
    refreshExpiry: number;
    algorithm: string;
    issuer: string;
    audience: string;
  };
  password: {
    minLength: number;
    requireNumbers: boolean;
    requireSpecialChars: boolean;
    requireUppercase: boolean;
    requireLowercase: boolean;
    maxAttempts: number;
    lockoutDuration: number;
  };
  authentication: {
    require2fa: boolean;
    requireFacialRecognition: boolean;
    requirePassword: boolean;
    allowedAdminRoles: string[];
    sessionTimeout: number;
    maxConcurrentSessions: number;
  };
  encryption: {
    algorithm: string;
    keySize: number;
    saltRounds: number;
  };
  cors: {
    enabled: boolean;
    allowedOrigins: string[];
    allowedMethods: string[];
    allowedHeaders: string[];
    exposedHeaders: string[];
    maxAge: number;
  };
}

export const DEFAULT_SECURITY_CONFIG: SecurityConfig = {
  token: {
    expiry: 3600,
    refreshExpiry: 604800,
    algorithm: 'HS256',
    issuer: 'cerno-id',
    audience: 'cerno-id-users',
  },
  password: {
    minLength: 8,
    requireNumbers: true,
    requireSpecialChars: true,
    requireUppercase: true,
    requireLowercase: true,
    maxAttempts: 5,
    lockoutDuration: 900,
  },
  authentication: {
    require2fa: false,
    requireFacialRecognition: false,
    requirePassword: true,
    allowedAdminRoles: ['admin', 'superadmin'],
    sessionTimeout: 3600,
    maxConcurrentSessions: 3,
  },
  encryption: {
    algorithm: 'aes-256-gcm',
    keySize: 32,
    saltRounds: 10,
  },
  cors: {
    enabled: true,
    allowedOrigins: ['http://localhost:3000'],
    allowedMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization'],
    exposedHeaders: ['Content-Range', 'X-Content-Range'],
    maxAge: 86400,
  },
}; 