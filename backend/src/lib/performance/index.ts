import { useEffect, useRef, useCallback, useState } from 'react'

// Add custom type declarations for Performance API
declare global {
  interface Performance {
    memory?: {
      usedJSHeapSize: number
      totalJSHeapSize: number
      jsHeapSizeLimit: number
    }
  }
  
  interface PerformanceEntry {
    initiatorType?: string
    value?: number
  }
}

interface PerformanceMetrics {
  componentName: string
  renderTime: number
  renderCount: number
  lastRenderTimestamp: number
  memoryUsage?: {
    usedHeap: number
    totalHeap: number
    heapLimit: number
  }
  longTaskCount?: number
  lifecycleEvents: {
    mount?: number
    unmount?: number
    update?: number[]
  }
  interactionMetrics?: {
    clicks: number
    keyPresses: number
    lastInteraction: number
  }
  resourceMetrics?: {
    scriptTime?: number
    layoutTime?: number
    recalcStyleTime?: number
  }
}

interface PerformanceOptions {
  enableMemoryTracking?: boolean
  enableLongTaskTracking?: boolean
  enableInteractionTracking?: boolean
  enableResourceTracking?: boolean
  warnThreshold?: number
  errorThreshold?: number
  samplingRate?: number
}

const metrics = new Map<string, PerformanceMetrics>()
const DEFAULT_WARN_THRESHOLD = 16.67
const DEFAULT_ERROR_THRESHOLD = 50
const DEFAULT_SAMPLING_RATE = 0.1

export function usePerformanceMonitor(
  componentName: string,
  options: PerformanceOptions = {}
) {
  const renderCount = useRef(0)
  const startTime = useRef(performance.now())
  const longTaskCount = useRef(0)
  const mountTime = useRef<number | null>(null)
  const interactionMetrics = useRef({
    clicks: 0,
    keyPresses: 0,
    lastInteraction: 0
  })
  const [isTracking, setIsTracking] = useState(false)

  const {
    enableMemoryTracking = false,
    enableLongTaskTracking = false,
    enableInteractionTracking = false,
    enableResourceTracking = false,
    warnThreshold = DEFAULT_WARN_THRESHOLD,
    errorThreshold = DEFAULT_ERROR_THRESHOLD,
    samplingRate = DEFAULT_SAMPLING_RATE
  } = options

  const checkMemoryUsage = useCallback(() => {
    if (performance.memory) {
      return {
        usedHeap: performance.memory.usedJSHeapSize / 1024 / 1024,
        totalHeap: performance.memory.totalJSHeapSize / 1024 / 1024,
        heapLimit: performance.memory.jsHeapSizeLimit / 1024 / 1024
      }
    }
    return undefined
  }, [])

  const checkResourceMetrics = useCallback(() => {
    if (!enableResourceTracking) return undefined

    const entries = performance.getEntriesByType('resource')
    const scriptTime = entries
      .filter(entry => entry.initiatorType === 'script')
      .reduce((total, entry) => total + entry.duration, 0)

    const layoutEntries = performance.getEntriesByType('layout-shift')
    const layoutTime = layoutEntries.reduce((total, entry: any) => total + entry.value, 0)

    return {
      scriptTime,
      layoutTime,
      recalcStyleTime: performance.now() - startTime.current
    }
  }, [enableResourceTracking])

  const trackInteraction = useCallback((type: 'click' | 'keypress') => {
    if (!enableInteractionTracking) return

    interactionMetrics.current = {
      ...interactionMetrics.current,
      [type === 'click' ? 'clicks' : 'keyPresses']: 
        interactionMetrics.current[type === 'click' ? 'clicks' : 'keyPresses'] + 1,
      lastInteraction: performance.now()
    }
  }, [enableInteractionTracking])

  useEffect(() => {
    // Only track a sample of component instances based on sampling rate
    if (Math.random() > samplingRate) return
    setIsTracking(true)

    mountTime.current = performance.now()
    const currentMetrics = {
      componentName,
      renderTime: 0,
      renderCount: 0,
      lastRenderTimestamp: Date.now(),
      lifecycleEvents: {
        mount: mountTime.current
      }
    }
    metrics.set(componentName, currentMetrics)

    if (enableInteractionTracking) {
      window.addEventListener('click', () => trackInteraction('click'))
      window.addEventListener('keypress', () => trackInteraction('keypress'))
    }

    return () => {
      if (enableInteractionTracking) {
        window.removeEventListener('click', () => trackInteraction('click'))
        window.removeEventListener('keypress', () => trackInteraction('keypress'))
      }

      const finalMetrics = metrics.get(componentName)
      if (finalMetrics?.lifecycleEvents) {
        finalMetrics.lifecycleEvents.unmount = performance.now()
        metrics.set(componentName, finalMetrics)
      }
    }
  }, [componentName, enableInteractionTracking, samplingRate, trackInteraction])

  useEffect(() => {
    if (!isTracking) return

    const renderTime = performance.now() - startTime.current
    renderCount.current += 1

    if (enableLongTaskTracking && renderTime > warnThreshold) {
      longTaskCount.current += 1
    }

    const currentMetrics = {
      componentName,
      renderTime,
      renderCount: renderCount.current,
      lastRenderTimestamp: Date.now(),
      ...(enableMemoryTracking && { memoryUsage: checkMemoryUsage() }),
      ...(enableLongTaskTracking && { longTaskCount: longTaskCount.current }),
      lifecycleEvents: {
        ...metrics.get(componentName)?.lifecycleEvents,
        update: [...(metrics.get(componentName)?.lifecycleEvents?.update || []), renderTime]
      },
      ...(enableInteractionTracking && { interactionMetrics: interactionMetrics.current }),
      ...(enableResourceTracking && { resourceMetrics: checkResourceMetrics() })
    }

    metrics.set(componentName, currentMetrics)

    if (renderTime > errorThreshold) {
      console.error(
        `Critical performance issue in ${componentName}: ${renderTime.toFixed(2)}ms`,
        currentMetrics
      )
    } else if (renderTime > warnThreshold) {
      console.warn(
        `Slow render detected in ${componentName}: ${renderTime.toFixed(2)}ms`,
        currentMetrics
      )
    }

    startTime.current = performance.now()
  })

  return {
    metrics: isTracking ? metrics.get(componentName) : undefined,
    allMetrics: Array.from(metrics.values())
  }
}

export function getComponentMetrics(componentName: string) {
  return metrics.get(componentName)
}

export function getAllMetrics() {
  return Array.from(metrics.values())
}

export function clearMetrics() {
  metrics.clear()
}

// Export types
export type { PerformanceMetrics, PerformanceOptions } 