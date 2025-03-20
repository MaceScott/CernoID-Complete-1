import { useEffect } from 'react';
import { serviceRegistry } from '../lib/service-registry';

export function useServices() {
  useEffect(() => {
    // Initialize services when component mounts
    return () => {
      // Cleanup services when component unmounts
      serviceRegistry.shutdown();
    };
  }, []);

  return {
    api: serviceRegistry.get('api'),
    ws: serviceRegistry.get('ws'),
    config: serviceRegistry.get('config'),
    logging: serviceRegistry.get('logging'),
    performance: serviceRegistry.get('performance'),
  };
}

// Type-safe service hooks
export function useApi() {
  return serviceRegistry.get('api');
}

export function useWebSocket() {
  return serviceRegistry.get('ws');
}

export function useConfig() {
  return serviceRegistry.get('config');
}

export function useLogging() {
  return serviceRegistry.get('logging');
}

export function usePerformance() {
  return serviceRegistry.get('performance');
} 