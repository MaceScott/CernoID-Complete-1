import { useState, useEffect } from 'react'
import { apiClient } from '../api/api-client'
import { Camera, Alert, SystemStatus } from '@/types'

interface UseDataOptions<T> {
  initialData?: T
  enabled?: boolean
  refetchInterval?: number
  onSuccess?: (data: T) => void
  onError?: (error: Error) => void
}

function useData<T>(
  fetcher: () => Promise<T>,
  options: UseDataOptions<T> = {}
) {
  const {
    initialData,
    enabled = true,
    refetchInterval,
    onSuccess,
    onError,
  } = options

  const [data, setData] = useState<T | undefined>(initialData)
  const [error, setError] = useState<Error | null>(null)
  const [isLoading, setIsLoading] = useState(!initialData && enabled)

  useEffect(() => {
    if (!enabled) return

    let mounted = true
    let timeoutId: NodeJS.Timeout | undefined

    async function fetchData() {
      try {
        setIsLoading(true)
        setError(null)
        const result = await fetcher()
        if (mounted) {
          setData(result)
          onSuccess?.(result)
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err : new Error('An error occurred'))
          onError?.(err as Error)
        }
      } finally {
        if (mounted) {
          setIsLoading(false)
        }
      }
    }

    fetchData()

    if (refetchInterval) {
      timeoutId = setInterval(fetchData, refetchInterval)
    }

    return () => {
      mounted = false
      if (timeoutId) clearInterval(timeoutId)
    }
  }, [enabled, fetcher, refetchInterval, onSuccess, onError])

  return { data, error, isLoading }
}

// Custom hooks for specific data types
export function useCameras(options?: UseDataOptions<Camera[]>) {
  return useData(() => apiClient.cameras.list(), options)
}

export function useAlerts(options?: UseDataOptions<Alert[]>) {
  return useData(() => apiClient.alerts.list(), options)
}

export function useSystemStatus(options?: UseDataOptions<SystemStatus>) {
  return useData(() => apiClient.system.getStatus(), {
    refetchInterval: 30000, // Refresh every 30 seconds
    ...options,
  })
} 