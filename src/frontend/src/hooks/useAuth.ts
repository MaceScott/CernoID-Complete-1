import { useState, useCallback, useEffect } from 'react';
import { User } from '../types/user';
import { AuthService } from '../services/auth';

export const useAuth = () => {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const checkAuth = useCallback(async () => {
        try {
            setLoading(true);
            const userData = await AuthService.checkAuth();
            setUser(userData);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Authentication failed');
            setUser(null);
        } finally {
            setLoading(false);
        }
    }, []);

    const login = useCallback(async (username: string, password: string) => {
        try {
            setLoading(true);
            const userData = await AuthService.login(username, password);
            setUser(userData);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Login failed');
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    const logout = useCallback(async () => {
        try {
            setLoading(true);
            await AuthService.logout();
            setUser(null);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Logout failed');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        checkAuth();
    }, [checkAuth]);

    return {
        user,
        loading,
        error,
        isAuthenticated: !!user,
        login,
        logout,
        checkAuth
    };
}; 