import { useState, useCallback } from 'react';
import { apiClient } from '../api/api-client';
import { User, PaginatedResponse } from '@/types';

interface UserFilters {
    search?: string;
    role?: string;
    status?: string;
    page?: number;
    limit?: number;
}

interface UseUsersReturn {
    users: User[];
    loading: boolean;
    error: string | null;
    total: number;
    page: number;
    limit: number;
    fetchUsers: (filters?: UserFilters) => Promise<void>;
    createUser: (userData: Partial<User>) => Promise<User>;
    updateUser: (userId: string, userData: Partial<User>) => Promise<User>;
    deleteUser: (userId: string) => Promise<void>;
}

export const useUsers = (): UseUsersReturn => {
    const [users, setUsers] = useState<User[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [limit, setLimit] = useState(10);

    const fetchUsers = useCallback(async (filters?: UserFilters) => {
        try {
            setLoading(true);
            setError(null);
            const response = await apiClient.users.list(filters);
            setUsers(response.items);
            setTotal(response.total);
            setPage(response.page);
            setLimit(response.limit);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    const createUser = useCallback(async (userData: Partial<User>) => {
        try {
            setLoading(true);
            setError(null);
            const user = await apiClient.users.create(userData);
            setUsers(prev => [...prev, user]);
            return user;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    const updateUser = useCallback(async (userId: string, userData: Partial<User>) => {
        try {
            setLoading(true);
            setError(null);
            const user = await apiClient.users.update(userId, userData);
            setUsers(prev => prev.map(u => u.id === userId ? user : u));
            return user;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    const deleteUser = useCallback(async (userId: string) => {
        try {
            setLoading(true);
            setError(null);
            await apiClient.users.delete(userId);
            setUsers(prev => prev.filter(u => u.id !== userId));
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    return {
        users,
        loading,
        error,
        total,
        page,
        limit,
        fetchUsers,
        createUser,
        updateUser,
        deleteUser
    };
}; 