import { useState, useCallback, useEffect } from 'react';
import { api } from '../services/api';
import { AppSettings } from '../types';
import { useApp } from '../context/AppContext';

export const useSettings = () => {
    const { dispatch } = useApp();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [settings, setSettings] = useState<AppSettings | null>(null);

    const fetchSettings = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            const response = await api.get<AppSettings>('/settings');
            setSettings(response.data);
            dispatch({ type: 'SET_SETTINGS', payload: response.data });
            return response.data;
        } catch (err: any) {
            setError(err.response?.data?.message || 'Failed to fetch settings');
            throw err;
        } finally {
            setLoading(false);
        }
    }, [dispatch]);

    const updateSettings = useCallback(async (
        updates: Partial<AppSettings>
    ) => {
        setLoading(true);
        setError(null);

        try {
            const response = await api.put<AppSettings>('/settings', updates);
            dispatch({ type: 'SET_SETTINGS', payload: response.data });
            return response.data;
        } catch (err: any) {
            setError(err.response?.data?.message || 'Failed to update settings');
            throw err;
        } finally {
            setLoading(false);
        }
    }, [dispatch]);

    const resetSettings = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            const response = await api.post<AppSettings>('/settings/reset');
            dispatch({ type: 'SET_SETTINGS', payload: response.data });
            return response.data;
        } catch (err: any) {
            setError(err.response?.data?.message || 'Failed to reset settings');
            throw err;
        } finally {
            setLoading(false);
        }
    }, [dispatch]);

    useEffect(() => {
        const loadSettings = async () => {
            try {
                const response = await api.get<AppSettings>('/settings');
                setSettings(response.data);
                dispatch({ type: 'SET_SETTINGS', payload: response.data });
            } catch (err: any) {
                setError(err.response?.data?.message || 'Failed to fetch settings');
            }
        };
        loadSettings();
    }, [dispatch]);

    return {
        settings,
        loading,
        error,
        fetchSettings,
        updateSettings,
        resetSettings
    };
}; 