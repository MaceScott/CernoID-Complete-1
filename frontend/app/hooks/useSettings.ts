import { useState, useEffect } from 'react';
import { api } from '@/services/api';
import { AppSettings } from '@/types/config/settings';

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
        tokenExpiry: 30,
        maxAttempts: 3,
        lockoutDuration: 15,
        require2fa: false,
        requireFacialRecognition: true,
        requirePassword: true,
        allowedAdminRoles: ['admin', 'security']
    },
    display: {
        density: 'comfortable',
        fontSize: 14,
        showThumbnails: true
    },
    recognition: {
        confidenceThreshold: 0.5,
        maxFaces: 10,
        useGpu: true,
        modelType: 'default',
        detectLandmarks: true,
        extractDescriptor: true
    },
    camera: {
        defaultDevice: '',
        resolution: '1280x720',
        fps: 30,
        quality: 80
    },
    system: {
        autoStart: false,
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