'use client';

import { useState, useEffect } from 'react';
import { Alert } from '@/types';

export function useAlerts() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const response = await fetch('/api/alerts');
        if (!response.ok) {
          throw new Error('Failed to fetch alerts');
        }
        const data = await response.json();
        setAlerts(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch alerts');
      } finally {
        setLoading(false);
      }
    };

    fetchAlerts();
  }, []);

  const acknowledgeAlert = async (id: string) => {
    try {
      const response = await fetch(`/api/alerts/${id}/acknowledge`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error('Failed to acknowledge alert');
      }
      setAlerts((prev) =>
        prev.map((alert) =>
          alert.id === id
            ? { ...alert, status: 'read' }
            : alert
        )
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to acknowledge alert');
    }
  };

  const resolveAlert = async (id: string) => {
    try {
      const response = await fetch(`/api/alerts/${id}/resolve`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error('Failed to resolve alert');
      }
      setAlerts((prev) =>
        prev.map((alert) =>
          alert.id === id ? { ...alert, status: 'resolved' } : alert
        )
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resolve alert');
    }
  };

  return {
    alerts,
    loading,
    error,
    acknowledgeAlert,
    resolveAlert,
  };
} 