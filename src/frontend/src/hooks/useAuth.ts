import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { User } from '../types';

export const useAuth = () => {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();

    const login = useCallback(async (username: string, password: string) => {
        setLoading(true);
        setError(null);
        
        try {
            const response = await api.post('/auth/login', {
                username,
                password
            });
            
            const { access_token, user: userData } = response.data;
            
            // Store token
            localStorage.setItem('token', access_token);
            
            // Update user state
            setUser(userData);
            
            // Navigate to dashboard
            navigate('/dashboard');
        } catch (err: any) {
            setError(err.response?.data?.message || 'Login failed');
            throw err;
        } finally {
            setLoading(false);
        }
    }, [navigate]);

    const logout = useCallback(async () => {
        try {
            await api.post('/auth/logout');
        } catch (err) {
            console.error('Logout error:', err);
        } finally {
            // Clear local storage
            localStorage.removeItem('token');
            
            // Reset state
            setUser(null);
            
            // Navigate to login
            navigate('/login');
        }
    }, [navigate]);

    const checkAuth = useCallback(async () => {
        const token = localStorage.getItem('token');
        if (!token) {
            return false;
        }

        try {
            const response = await api.get('/auth/me');
            setUser(response.data);
            return true;
        } catch (err) {
            localStorage.removeItem('token');
            return false;
        }
    }, []);

    return {
        user,
        loading,
        error,
        login,
        logout,
        checkAuth
    };
}; 