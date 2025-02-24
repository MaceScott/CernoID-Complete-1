import { useEffect, useRef } from 'react'

interface PerformanceMetrics {
  componentName: string
  renderTime: number
  renderCount: number
  lastRenderTimestamp: number
}

const metrics = new Map<string, PerformanceMetrics>()

export function usePerformanceMonitor(componentName: string) {
  const renderCount = useRef(0)
  const startTime = useRef(performance.now())

  useEffect(() => {
    const renderTime = performance.now() - startTime.current
    renderCount.current += 1

    metrics.set(componentName, {
      componentName,
      renderTime,
      renderCount: renderCount.current,
      lastRenderTimestamp: Date.now()
    })

    // Log if render time is concerning
    if (renderTime > 16.67) { // More than 60fps threshold
      console.warn(`Slow render detected in ${componentName}: ${renderTime.toFixed(2)}ms`)
    }

    // Reset for next render
    startTime.current = performance.now()
  })
}

export function getPerformanceMetrics() {
  return Array.from(metrics.values())
} 