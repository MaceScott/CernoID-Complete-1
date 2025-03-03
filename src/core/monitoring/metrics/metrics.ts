import { register, Counter, Histogram } from 'prom-client'

// Request counter
export const httpRequestsTotal = new Counter({
  name: 'http_requests_total',
  help: 'Total number of HTTP requests',
  labelNames: ['method', 'path', 'status']
})

// Response time histogram
export const httpRequestDuration = new Histogram({
  name: 'http_request_duration_seconds',
  help: 'HTTP request duration in seconds',
  labelNames: ['method', 'path', 'status'],
  buckets: [0.1, 0.5, 1, 2, 5]
})

// Camera metrics
export const activeCameras = new Counter({
  name: 'active_cameras_total',
  help: 'Total number of active cameras'
})

// Alert metrics
export const alertsGenerated = new Counter({
  name: 'alerts_generated_total',
  help: 'Total number of alerts generated',
  labelNames: ['type', 'priority']
})

// System metrics
export const systemMetrics = {
  cpuUsage: new Gauge({
    name: 'system_cpu_usage',
    help: 'System CPU usage percentage'
  }),
  memoryUsage: new Gauge({
    name: 'system_memory_usage',
    help: 'System memory usage in bytes'
  }),
  diskUsage: new Gauge({
    name: 'system_disk_usage',
    help: 'System disk usage in bytes'
  })
}

// Export metrics
export async function getMetrics() {
  return register.metrics()
} 