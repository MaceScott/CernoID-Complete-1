import { useState, useCallback } from 'react';
import { api } from '../services/api';
import { User, PaginatedResponse } from '../types';

interface UserFilters {
    role?: string;
    isActive?: boolean;
    search?: string;
}

export const useUsers = () => {
    const [users, setUsers] = useState<User[]>([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchUsers = useCallback(async (
        page: number = 1,
        limit: number = 10,
        filters?: UserFilters
    ) => {
        setLoading(true);
        setError(null);

        try {
            const response = await api.get<PaginatedResponse<User>>('/users', {
                params: {
                    page,
                    limit,
                    ...filters
                }
            });

            setUsers(response.data.items);
            setTotal(response.data.total);
        } catch (err: any) {
            setError(err.response?.data?.message || 'Failed to fetch users');
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    const createUser = useCallback(async (userData: Partial<User>) => {
        setLoading(true);
        setError(null);

        try {
            const response = await api.post<User>('/users', userData);
            setUsers(prev => [...prev, response.data]);
            return response.data;
        } catch (err: any) {
            setError(err.response?.data?.message || 'Failed to create user');
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    const updateUser = useCallback(async (
        userId: number,
        updates: Partial<User>
    ) => {
        setLoading(true);
        setError(null);

        try {
            const response = await api.put<User>(`/users/${userId}`, updates);
            setUsers(prev => 
                prev.map(user => 
                    user.id === userId ? response.data : user
                )
            );
            return response.data;
        } catch (err: any) {
            setError(err.response?.data?.message || 'Failed to update user');
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    const deleteUser = useCallback(async (userId: number) => {
        setLoading(true);
        setError(null);

        try {
            await api.delete(`/users/${userId}`);
            setUsers(prev => prev.filter(user => user.id !== userId));
        } catch (err: any) {
            setError(err.response?.data?.message || 'Failed to delete user');
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    return {
        users,
        total,
        loading,
        error,
        fetchUsers,
        createUser,
        updateUser,
        deleteUser
    };
}; 