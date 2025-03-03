export interface User {
  id: string
  name: string
  email: string
  role: "admin" | "user"
  createdAt: string
  lastLogin: string
  status: "active" | "inactive"
}

export interface Camera {
  id: string
  name: string
  location: string
  status: "active" | "inactive"
  type: "indoor" | "outdoor"
  resolution: string
  lastActive: string
}

export interface Alert {
  id: string
  type: "motion" | "face" | "system" | "error"
  message: string
  timestamp: string
  status: "new" | "read" | "resolved"
  priority: "low" | "medium" | "high"
  cameraId?: string
}

export interface SystemStatus {
  cpu: number
  memory: number
  storage: number
  uptime: string
  lastUpdate: string
  services: {
    name: string
    status: "operational" | "degraded" | "down"
    lastCheck: string
  }[]
}

export interface Face {
  id: string
  bbox: number[]
  confidence: number
  landmarks?: number[][]
  features?: number[]
  personId?: string
  timestamp: string
} 