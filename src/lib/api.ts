import { User, Camera, Alert, SystemStatus } from "@/types"

class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: any
  ) {
    super(message)
    this.name = "APIError"
  }
}

async function fetchAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`/api${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  })

  const data = await response.json()

  if (!response.ok) {
    throw new APIError(
      data.error || "An error occurred",
      response.status,
      data
    )
  }

  return data
}

export const api = {
  auth: {
    login: (email: string, password: string) =>
      fetchAPI<{ user: User; token: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }),
    logout: () =>
      fetchAPI("/auth/logout", { method: "POST" }),
  },
  system: {
    getStatus: () =>
      fetchAPI<SystemStatus>("/system/status"),
  },
  cameras: {
    list: () =>
      fetchAPI<Camera[]>("/cameras"),
    getById: (id: string) =>
      fetchAPI<Camera>(`/cameras/${id}`),
    update: (id: string, data: Partial<Camera>) =>
      fetchAPI<Camera>(`/cameras/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
  },
  alerts: {
    list: () =>
      fetchAPI<Alert[]>("/alerts"),
    markAsRead: (id: string) =>
      fetchAPI<Alert>(`/alerts/${id}/read`, { method: "POST" }),
  },
} 