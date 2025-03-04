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

export interface AppSettings {
  recognition: {
    min_confidence: number
    max_faces: number
    use_gpu: boolean
    model_type: string
  }
  security: {
    token_expiry: number
    max_attempts: number
    lockout_duration: number
    require_2fa: boolean
  }
  performance: {
    batch_size: number
    cache_enabled: boolean
    cache_size: number
    worker_threads: number
  }
  monitoring: {
    metrics_enabled: boolean
    log_level: string
    retention_days: number
    alert_threshold: number
  }
}

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    limit: number;
    pages: number;
} 