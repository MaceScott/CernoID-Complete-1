export interface ApiConfig {
  baseUrl: string;
  version: string;
  timeout: number;
  retries: number;
  rateLimit: {
    enabled: boolean;
    maxRequests: number;
    windowMs: number;
  };
  endpoints: {
    auth: {
      login: string;
      logout: string;
      refresh: string;
      register: string;
      verify: string;
    };
    recognition: {
      detect: string;
      register: string;
      verify: string;
      search: string;
    };
    camera: {
      list: string;
      status: string;
      stream: string;
      alerts: string;
    };
    system: {
      status: string;
      metrics: string;
      logs: string;
    };
  };
  headers: {
    'Content-Type': string;
    Accept: string;
  };
}

export const DEFAULT_API_CONFIG: ApiConfig = {
  baseUrl: 'http://localhost:3000/api',
  version: 'v1',
  timeout: 30000,
  retries: 3,
  rateLimit: {
    enabled: true,
    maxRequests: 100,
    windowMs: 60000,
  },
  endpoints: {
    auth: {
      login: '/auth/login',
      logout: '/auth/logout',
      refresh: '/auth/refresh',
      register: '/auth/register',
      verify: '/auth/verify',
    },
    recognition: {
      detect: '/recognition/detect',
      register: '/recognition/register',
      verify: '/recognition/verify',
      search: '/recognition/search',
    },
    camera: {
      list: '/cameras',
      status: '/cameras/status',
      stream: '/cameras/stream',
      alerts: '/cameras/alerts',
    },
    system: {
      status: '/system/status',
      metrics: '/system/metrics',
      logs: '/system/logs',
    },
  },
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
}; 