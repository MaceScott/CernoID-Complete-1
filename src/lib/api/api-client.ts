import { User, Camera, Alert, SystemStatus } from "@/types"

class APIClient {
  private static instance: APIClient
  private token: string | null = null
  private abortControllers: Map<string, AbortController> = new Map()

  private constructor() {
    // Initialize from localStorage/cookies if needed
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('authToken')
    }
  }

  static getInstance(): APIClient {
    if (!APIClient.instance) {
      APIClient.instance = new APIClient()
    }
    return APIClient.instance
  }

  setToken(token: string) {
    this.token = token
    if (typeof window !== 'undefined') {
      localStorage.setItem('authToken', token)
    }
  }

  clearToken() {
    this.token = null
    if (typeof window !== 'undefined') {
      localStorage.removeItem('authToken')
    }
  }

  private async fetch<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    // Cancel any existing request to this endpoint
    this.abortControllers.get(endpoint)?.abort()
    const controller = new AbortController()
    this.abortControllers.set(endpoint, controller)

    try {
      const response = await fetch(`/api${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...(this.token ? { Authorization: `Bearer ${this.token}` } : {}),
          ...options.headers,
        },
        signal: controller.signal,
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'An error occurred')
      }

      return data
    } finally {
      this.abortControllers.delete(endpoint)
    }
  }

  // Auth endpoints
  auth = {
    login: async (email: string, password: string) => {
      const data = await this.fetch<{ token: string; user: User }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      })
      this.setToken(data.token)
      return data
    },

    logout: async () => {
      await this.fetch('/auth/logout', { method: 'POST' })
      this.clearToken()
    },
  }

  // Camera endpoints
  cameras = {
    list: () => this.fetch<Camera[]>('/cameras'),
    get: (id: string) => this.fetch<Camera>(`/cameras/${id}`),
    update: (id: string, data: Partial<Camera>) =>
      this.fetch<Camera>(`/cameras/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
  }

  // Alert endpoints
  alerts = {
    list: () => this.fetch<Alert[]>('/alerts'),
    get: (id: string) => this.fetch<Alert>(`/alerts/${id}`),
    resolve: (id: string) =>
      this.fetch<Alert>(`/alerts/${id}/resolve`, { method: 'POST' }),
  }

  // System endpoints
  system = {
    getStatus: () => this.fetch<SystemStatus>('/system/status'),
    updateSettings: (settings: any) =>
      this.fetch('/system/settings', {
        method: 'PUT',
        body: JSON.stringify(settings),
      }),
  }
}

export const apiClient = APIClient.getInstance() 