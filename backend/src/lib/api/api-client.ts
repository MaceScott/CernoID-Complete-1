import { User, Camera, Alert, SystemStatus, AppSettings } from "@/types"
import { RecognitionResult } from "../types/recognition"
import { AxiosError, AxiosResponse } from 'axios'

interface ApiError {
    message: string;
    code?: string;
    details?: unknown;
}

interface ApiResponse<T> {
    data: T;
    status: number;
    message?: string;
}

interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    limit: number;
    pages: number;
}

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

  async handleError(error: AxiosError<ApiError>): Promise<never> {
    const errorMessage = error.response?.data?.message || error.message;
    throw new Error(errorMessage);
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

  // Recognition endpoints
  recognition = {
    processImage: (imageData: string) =>
      this.fetch<RecognitionResult>('/recognition/process', {
        method: 'POST',
        body: JSON.stringify({ image: imageData }),
      }),
  }

  // Settings endpoints
  settings = {
    get: () => this.fetch<AppSettings>('/settings'),
    update: (settings: AppSettings) =>
      this.fetch<AppSettings>('/settings', {
        method: 'PUT',
        body: JSON.stringify(settings),
      }),
    reset: () => this.fetch<AppSettings>('/settings/reset', { method: 'POST' }),
  }

  // Users endpoints
  users = {
    list: (filters?: {
      search?: string;
      role?: string;
      status?: string;
      page?: number;
      limit?: number;
    }) => this.fetch<PaginatedResponse<User>>('/users', {
      method: 'GET',
      ...(filters && { body: JSON.stringify(filters) })
    }),
    get: (id: string) => this.fetch<User>(`/users/${id}`),
    create: (userData: Partial<User>) =>
      this.fetch<User>('/users', {
        method: 'POST',
        body: JSON.stringify(userData),
      }),
    update: (id: string, userData: Partial<User>) =>
      this.fetch<User>(`/users/${id}`, {
        method: 'PUT',
        body: JSON.stringify(userData),
      }),
    delete: (id: string) =>
      this.fetch<void>(`/users/${id}`, { method: 'DELETE' }),
  }
}

export const apiClient = APIClient.getInstance() 