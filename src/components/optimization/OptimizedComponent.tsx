import { memo, useEffect, useRef, useMemo } from 'react'
import { usePerformanceMonitor } from '@/lib/performance'

interface OptimizedComponentProps {
  name: string
  children: React.ReactNode
  dependencies?: any[]
  onPerformanceIssue?: (metrics: { renderTime: number, renderCount: number }) => void
}

function OptimizedComponentInner({
  name,
  children,
  dependencies = [],
  onPerformanceIssue
}: OptimizedComponentProps) {
  const { metrics } = usePerformanceMonitor(name)
  const renderCount = useRef(0)
  const lastRenderTime = useRef(0)

  useEffect(() => {
    renderCount.current += 1
    const currentTime = performance.now()
    const renderTime = currentTime - lastRenderTime.current
    
    // Alert if render takes too long
    if (renderTime > 16.67) { // 60fps threshold
      onPerformanceIssue?.({
        renderTime,
        renderCount: renderCount.current
      })
    }
    
    lastRenderTime.current = currentTime
  })

  // Memoize children if they are expensive to render
  const memoizedChildren = useMemo(
    () => children,
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [...dependencies]
  )

  return <>{memoizedChildren}</>
}

export const OptimizedComponent = memo(
  OptimizedComponentInner,
  (prev, next) => {
    // Deep comparison of dependencies
    if (prev.dependencies && next.dependencies) {
      return prev.dependencies.every(
        (dep, i) => next.dependencies && 
          JSON.stringify(dep) === JSON.stringify(next.dependencies[i])
      )
    }
    return true
  }
) 