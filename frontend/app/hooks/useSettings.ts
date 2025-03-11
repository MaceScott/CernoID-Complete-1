import { useState, useEffect } from 'react';
import { api } from '@/services/api';
import { AppSettings } from '@/types';

interface UseSettingsReturn {
    settings: AppSettings | null;
    loading: boolean;
    error: string | null;
    updateSettings: (newSettings: AppSettings) => Promise<void>;
    resetSettings: () => Promise<void>;
}

const defaultSettings: AppSettings = {
    theme: 'light',
    language: 'en',
    notifications: {
        enabled: true,
        sound: true,
        desktop: true
    },
    security: {
        token_expiry: 30,
        max_attempts: 3,
        lockout_duration: 15,
        require_2fa: false,
        require_facial_recognition: true,
        require_password: true,
        allowed_admin_roles: ['admin', 'security']
    },
    display: {
        density: 'comfortable',
        fontSize: 14,
        showThumbnails: true
    },
    recognition: {
        min_confidence: 0.5,
        max_faces: 10,
        use_gpu: true,
        model_type: 'default'
    },
    system: {
        autoUpdate: true,
        logLevel: 'info',
        retentionDays: 30
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