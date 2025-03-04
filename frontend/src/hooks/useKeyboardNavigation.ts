import { useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '@/context/AppContext';

interface ShortcutMap {
    key: string;
    ctrlKey?: boolean;
    action: () => void;
    description: string;
}

export const useKeyboardNavigation = () => {
    const navigate = useNavigate();
    const { user } = useApp();

    const shortcuts = useMemo(() => [
        {
            key: 'h',
            ctrlKey: true,
            action: () => navigate('/dashboard'),
            description: 'Go to Dashboard'
        },
        {
            key: 'r',
            ctrlKey: true,
            action: () => navigate('/recognition'),
            description: 'Go to Recognition'
        },
        {
            key: 'u',
            ctrlKey: true,
            action: () => user?.role === 'admin' && navigate('/users'),
            description: 'Go to User Management'
        },
        {
            key: 's',
            ctrlKey: true,
            action: () => user?.role === 'admin' && navigate('/settings'),
            description: 'Go to Settings'
        },
        {
            key: '/',
            action: () => document.querySelector<HTMLInputElement>('[role="search"]')?.focus(),
            description: 'Focus Search'
        }
    ], [navigate, user?.role]);

    const handleKeyPress = useCallback((event: KeyboardEvent) => {
        const shortcut = shortcuts.find(s => 
            s.key === event.key && 
            (!s.ctrlKey || (s.ctrlKey && event.ctrlKey))
        );

        if (shortcut) {
            event.preventDefault();
            shortcut.action();
        }
    }, [shortcuts]);

    useEffect(() => {
        window.addEventListener('keydown', handleKeyPress);
        return () => window.removeEventListener('keydown', handleKeyPress);
    }, [handleKeyPress]);

    return {
        shortcuts,
        isEnabled: true
    };
}; 