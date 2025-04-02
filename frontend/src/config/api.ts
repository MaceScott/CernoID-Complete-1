export const API_ENDPOINTS = {
  // Auth endpoints
  LOGIN: '/api/v1/auth/login',
  LOGOUT: '/api/v1/auth/logout',
  REFRESH_TOKEN: '/api/v1/auth/refresh',
  ME: '/api/v1/auth/me',

  // Person endpoints
  PERSONS: '/api/v1/persons',
  PERSON_BY_ID: (id: number) => `/api/v1/persons/${id}`,

  // Camera endpoints
  CAMERAS: '/api/v1/cameras',
  CAMERA_BY_ID: (id: number) => `/api/v1/cameras/${id}`,

  // Stream endpoints
  STREAM_STATUS: (id: number) => `/api/v1/streams/${id}/status`,
  STREAM_START: (id: number) => `/api/v1/streams/${id}/start`,
  STREAM_STOP: (id: number) => `/api/v1/streams/${id}/stop`,
  STREAM_CONFIG: (id: number) => `/api/v1/streams/${id}/config`,

  // Recognition endpoints
  VERIFY_FACE: (id: number) => `/api/v1/recognition/verify/${id}`,
  IDENTIFY_FACE: '/api/v1/recognition/identify',
  REGISTER_FACE: (id: number) => `/api/v1/recognition/register/${id}`,

  // System endpoints
  HEALTH: '/api/v1/system/health',
  SYSTEM_INFO: '/api/v1/system/info',
  METRICS: '/api/v1/system/metrics',

  // Security endpoints
  CHANGE_PASSWORD: '/api/v1/security/change-password',
  RESET_PASSWORD_REQUEST: '/api/v1/security/reset-password-request',
  RESET_PASSWORD: '/api/v1/security/reset-password'
} as const;

export type APIEndpoint = typeof API_ENDPOINTS[keyof typeof API_ENDPOINTS]; 