import { useState, useEffect } from 'react';
import { api } from '../services/api';
import { AppSettings } from '../types';

interface UseSettingsReturn {
    settings: AppSettings | null;
    loading: boolean;
    error: string | null;
    updateSettings: (newSettings: AppSettings) => Promise<void>;
    resetSettings: () => Promise<void>;
}

const defaultSettings: AppSettings = {
    recognition: {
        min_confidence: 0.5,
        max_faces: 10,
        use_gpu: true,
        model_type: 'default'
    },
    security: {
        token_expiry: 30,
        max_attempts: 3,
        lockout_duration: 15,
        require_2fa: false
    },
    performance: {
        batch_size: 16,
        cache_enabled: true,
        cache_size: 1000,
        worker_threads: 4
    },
    monitoring: {
        metrics_enabled: true,
        log_level: 'info',
        retention_days: 30,
        alert_threshold: 0.9
    }
};

export const useSettings = (): UseSettingsReturn => {
    const [settings, setSettings] = useState<AppSettings | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchSettings = async () => {
        try {
            setLoading(true);
            const response = await api.get('/settings');
            setSettings(response.data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
        } finally {
            setLoading(false);
        }
    };

    const updateSettings = async (newSettings: AppSettings) => {
        try {
            setLoading(true);
            await api.put('/settings', newSettings);
            setSettings(newSettings);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const resetSettings = async () => {
        try {
            setLoading(true);
            await api.post('/settings/reset');
            setSettings(defaultSettings);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchSettings();
    }, []);

    return {
        settings,
        loading,
        error,
        updateSettings,
        resetSettings
    };
}; 