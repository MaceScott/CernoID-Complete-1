import { useState, useEffect, useCallback } from 'react';
import { api } from '@/services/api';
import { ZoneAccess, AccessAlert, AccessLog, TimeSlot } from '@/types/access';
import { User } from '@/types/user';

interface UseAccessControlReturn {
    zones: ZoneAccess[];
    alerts: AccessAlert[];
    logs: AccessLog[];
    loading: boolean;
    error: string | null;
    checkAccess: (zoneId: string) => Promise<boolean>;
    requestAccess: (zoneId: string) => Promise<void>;
    resolveAlert: (alertId: string) => Promise<void>;
    dismissAlert: (alertId: string) => Promise<void>;
}

export const useAccessControl = (): UseAccessControlReturn => {
    const [zones, setZones] = useState<ZoneAccess[]>([]);
    const [alerts, setAlerts] = useState<AccessAlert[]>([]);
    const [logs, setLogs] = useState<AccessLog[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const isTimeInSlot = (time: Date, slot: TimeSlot): boolean => {
        const currentTime = time.getHours() * 60 + time.getMinutes();
        const [startHour, startMinute] = slot.start.split(':').map(Number);
        const [endHour, endMinute] = slot.end.split(':').map(Number);
        const slotStart = startHour * 60 + startMinute;
        const slotEnd = endHour * 60 + endMinute;
        const currentDay = time.getDay();

        return (
            currentTime >= slotStart &&
            currentTime <= slotEnd &&
            slot.days.includes(currentDay)
        );
    };

    const checkAccess = useCallback(async (zoneId: string): Promise<boolean> => {
        try {
            const response = await api.get(`/access/check/${zoneId}`);
            return response.data.hasAccess;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to check access');
            return false;
        }
    }, []);

    const requestAccess = useCallback(async (zoneId: string): Promise<void> => {
        try {
            setLoading(true);
            const response = await api.post(`/access/request/${zoneId}`);
            if (response.data.alert) {
                setAlerts(prev => [...prev, response.data.alert]);
            }
            if (response.data.log) {
                setLogs(prev => [...prev, response.data.log]);
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to request access');
        } finally {
            setLoading(false);
        }
    }, []);

    const resolveAlert = useCallback(async (alertId: string): Promise<void> => {
        try {
            setLoading(true);
            await api.post(`/access/alerts/${alertId}/resolve`);
            setAlerts(prev => prev.map(alert => 
                alert.id === alertId 
                    ? { ...alert, status: 'resolved', resolvedAt: new Date().toISOString() }
                    : alert
            ));
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to resolve alert');
        } finally {
            setLoading(false);
        }
    }, []);

    const dismissAlert = useCallback(async (alertId: string): Promise<void> => {
        try {
            setLoading(true);
            await api.post(`/access/alerts/${alertId}/dismiss`);
            setAlerts(prev => prev.map(alert => 
                alert.id === alertId 
                    ? { ...alert, status: 'dismissed' }
                    : alert
            ));
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to dismiss alert');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const [zonesResponse, alertsResponse, logsResponse] = await Promise.all([
                    api.get('/access/zones'),
                    api.get('/access/alerts'),
                    api.get('/access/logs')
                ]);
                setZones(zonesResponse.data);
                setAlerts(alertsResponse.data);
                setLogs(logsResponse.data);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to fetch access data');
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    return {
        zones,
        alerts,
        logs,
        loading,
        error,
        checkAccess,
        requestAccess,
        resolveAlert,
        dismissAlert
    };
}; 