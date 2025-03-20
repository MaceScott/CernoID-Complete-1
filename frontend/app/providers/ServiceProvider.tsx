'use client';

import { ReactNode, useEffect } from 'react';
import { serviceRegistry } from '../lib/service-registry';
import { loggingService } from '../lib/logging-service';

interface ServiceProviderProps {
  children: ReactNode;
}

export function ServiceProvider({ children }: ServiceProviderProps) {
  useEffect(() => {
    // Initialize services when the app starts
    loggingService.info('Initializing application services');

    return () => {
      // Cleanup services when the app unmounts
      serviceRegistry.shutdown();
    };
  }, []);

  return <>{children}</>;
} 