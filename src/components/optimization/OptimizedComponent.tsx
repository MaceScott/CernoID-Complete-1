import { memo, useEffect, useRef } from 'react'
import { usePerformanceMonitor } from '@/lib/performance'

interface OptimizedComponentProps {
  name: string
  children: React.ReactNode
  dependencies?: any[]
}

function OptimizedComponentInner({
  name,
  children,
  dependencies = []
}: OptimizedComponentProps) {
  usePerformanceMonitor(name)
  const renderCount = useRef(0)

  useEffect(() => {
    renderCount.current += 1
    if (renderCount.current > 1) {
      console.log(`${name} re-rendered. Render count: ${renderCount.current}`)
    }
  })

  return <>{children}</>
}

export const OptimizedComponent = memo(
  OptimizedComponentInner,
  (prev, next) => {
    // Custom comparison logic if needed
    if (prev.dependencies && next.dependencies) {
      return prev.dependencies.every(
        (dep, i) => dep === next.dependencies[i]
      )
    }
    return true
  }
) 