import { useState, useCallback, useEffect } from 'react';
import { api } from '../services/api';

interface MetricsData {
    total_requests: number;
    success_rate: number;
    avg_response_time: number;
    active_users: number;
    hourly_data: {
        time: string;
        requests: number;
        response_time: number;
        success_rate: number;
    }[];
}

export const useMetrics = (refreshInterval: number = 60000) => {
    const [metrics, setMetrics] = useState<MetricsData | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchMetrics = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            const response = await api.get<MetricsData>('/metrics');
            setMetrics(response.data);
        } catch (err: any) {
            setError(err.response?.data?.message || 'Failed to fetch metrics');
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchMetrics();

        // Set up periodic refresh
        if (refreshInterval > 0) {
            const intervalId = setInterval(fetchMetrics, refreshInterval);
            return () => clearInterval(intervalId);
        }
    }, [fetchMetrics, refreshInterval]);

    const getMetricsByDateRange = useCallback(async (
        startDate: Date,
        endDate: Date
    ) => {
        setLoading(true);
        setError(null);

        try {
            const response = await api.get<MetricsData>('/metrics/range', {
                params: {
                    start_date: startDate.toISOString(),
                    end_date: endDate.toISOString()
                }
            });
            return response.data;
        } catch (err: any) {
            setError(err.response?.data?.message || 'Failed to fetch metrics');
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    return {
        metrics,
        loading,
        error,
        fetchMetrics,
        getMetricsByDateRange
    };
}; 