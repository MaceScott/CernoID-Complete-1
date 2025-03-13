import { useState, useEffect } from 'react';

interface PerformanceMetrics {
  renderTime: number;
  renderCount: number;
  fps: number;
  memory?: {
    usedJSHeapSize: number;
    totalJSHeapSize: number;
  };
}

// Chrome-specific performance memory API
interface PerformanceMemory {
  memory: {
    usedJSHeapSize: number;
    totalJSHeapSize: number;
    jsHeapSizeLimit: number;
  };
}

export function usePerformanceMonitor(componentName: string) {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    renderTime: 0,
    renderCount: 0,
    fps: 60,
  });

  useEffect(() => {
    let frameCount = 0;
    let lastTime = performance.now();
    let animationFrameId: number;

    const measurePerformance = () => {
      const currentTime = performance.now();
      const elapsed = currentTime - lastTime;

      if (elapsed >= 1000) {
        const fps = Math.round((frameCount * 1000) / elapsed);
        
        const performanceMetrics: PerformanceMetrics = {
          renderTime: elapsed / frameCount,
          renderCount: frameCount,
          fps,
        };

        // Add memory info if available (Chrome only)
        const perfMemory = performance as unknown as PerformanceMemory;
        if (perfMemory.memory) {
          performanceMetrics.memory = {
            usedJSHeapSize: perfMemory.memory.usedJSHeapSize,
            totalJSHeapSize: perfMemory.memory.totalJSHeapSize,
          };
        }

        setMetrics(performanceMetrics);

        // Log performance issues
        if (fps < 30) {
          console.warn(`Performance issue detected in ${componentName}:`, performanceMetrics);
        }

        frameCount = 0;
        lastTime = currentTime;
      }

      frameCount++;
      animationFrameId = requestAnimationFrame(measurePerformance);
    };

    measurePerformance();

    return () => {
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
      }
    };
  }, [componentName]);

  return { metrics };
} 