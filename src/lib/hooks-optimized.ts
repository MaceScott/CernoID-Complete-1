import { useState, useEffect, useCallback, useMemo } from 'react'
import { apiClient } from './api-client'
import { cacheManager } from './cache'
import { usePerformanceMonitor } from './performance'
import type { User, Camera, Alert, SystemStatus } from '@/types'

interface UseDataOptions<T> {
  key: string
  ttl?: number
  initialData?: T
  enabled?: boolean
  refetchInterval?: number
  onSuccess?: (data: T) => void
  onError?: (error: Error) => void
}

function useData<T>(
  fetcher: () => Promise<T>,
  options: UseDataOptions<T>
) {
  const {
    key,
    ttl,
    initialData,
    enabled = true,
    refetchInterval,
    onSuccess,
    onError,
  } = options

  const [data, setData] = useState<T | undefined>(() => {
    const cached = cacheManager.get<T>(key)
    return cached ?? initialData
  })
  const [error, setError] = useState<Error | null>(null)
  const [isLoading, setIsLoading] = useState(!initialData && enabled)

  // Memoize the fetch function
  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      // Check cache first
      const cached = cacheManager.get<T>(key)
      if (cached) {
        setData(cached)
        setIsLoading(false)
        return
      }

      const result = await fetcher()
      cacheManager.set(key, result, ttl)
      setData(result)
      onSuccess?.(result)
    } catch (err) {
      const error = err instanceof Error ? err : new Error('An error occurred')
      setError(error)
      onError?.(error)
    } finally {
      setIsLoading(false)
    }
  }, [key, ttl, fetcher, onSuccess, onError])

  useEffect(() => {
    if (!enabled) return

    let timeoutId: NodeJS.Timeout | undefined

    fetchData()

    if (refetchInterval) {
      timeoutId = setInterval(fetchData, refetchInterval)
    }

    return () => {
      if (timeoutId) clearInterval(timeoutId)
    }
  }, [enabled, fetchData, refetchInterval])

  const refetch = useCallback(() => {
    cacheManager.invalidate(key)
    return fetchData()
  }, [key, fetchData])

  return { data, error, isLoading, refetch }
}

// Optimized hooks with caching
export function useCameras(options?: Partial<UseDataOptions<Camera[]>>) {
  usePerformanceMonitor('useCameras')
  
  return useData(() => apiClient.cameras.list(), {
    key: 'cameras',
    ttl: 30000, // 30 seconds
    ...options,
  })
}

export function useAlerts(options?: Partial<UseDataOptions<Alert[]>>) {
  usePerformanceMonitor('useAlerts')
  
  return useData(() => apiClient.alerts.list(), {
    key: 'alerts',
    ttl: 10000, // 10 seconds
    ...options,
  })
}

export function useSystemStatus(options?: Partial<UseDataOptions<SystemStatus>>) {
  usePerformanceMonitor('useSystemStatus')
  
  return useData(() => apiClient.system.getStatus(), {
    key: 'system-status',
    ttl: 5000, // 5 seconds
    refetchInterval: 30000, // Refresh every 30 seconds
    ...options,
  })
} 