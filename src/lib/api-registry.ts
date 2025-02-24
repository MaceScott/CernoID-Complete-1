// Centralized API endpoint management
export const apiEndpoints = {
  auth: {
    login: '/api/auth/login',
    logout: '/api/auth/logout',
    verify: '/api/auth/verify',
  },
  users: {
    list: '/api/users',
    create: '/api/users',
    get: (id: string) => `/api/users/${id}`,
    update: (id: string) => `/api/users/${id}`,
    delete: (id: string) => `/api/users/${id}`,
  },
  cameras: {
    list: '/api/cameras',
    create: '/api/cameras',
    get: (id: string) => `/api/cameras/${id}`,
    update: (id: string) => `/api/cameras/${id}`,
    delete: (id: string) => `/api/cameras/${id}`,
    stream: (id: string) => `/api/cameras/${id}/stream`,
  },
  alerts: {
    list: '/api/alerts',
    get: (id: string) => `/api/alerts/${id}`,
    resolve: (id: string) => `/api/alerts/${id}/resolve`,
  },
  system: {
    status: '/api/system/status',
    settings: '/api/system/settings',
  },
} as const

// Type-safe API response types
export interface APIResponse<T> {
  data: T
  error?: never
}

export interface APIError {
  data?: never
  error: {
    message: string
    code: string
  }
}

export type APIResult<T> = APIResponse<T> | APIError 