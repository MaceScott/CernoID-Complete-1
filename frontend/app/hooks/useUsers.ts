import { useState, useEffect } from 'react';

interface User {
    id: string;
    username: string;
    email: string;
    role: string;
    status: 'active' | 'inactive' | 'suspended';
    lastLogin?: string;
    createdAt: string;
    updatedAt: string;
}

interface UserFormData {
    username: string;
    email: string;
    role: string;
    password?: string;
}

interface UseUsersReturn {
    users: User[];
    loading: boolean;
    error: string | null;
    createUser: (userData: UserFormData) => Promise<void>;
    updateUser: (id: string, userData: Partial<UserFormData>) => Promise<void>;
    deleteUser: (id: string) => Promise<void>;
    getUser: (id: string) => Promise<User>;
}

export const useUsers = (): UseUsersReturn => {
    const [users, setUsers] = useState<User[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchUsers = async () => {
        try {
            setLoading(true);
            const response = await fetch('/api/users');
            if (!response.ok) {
                throw new Error('Failed to fetch users');
            }
            const data = await response.json();
            setUsers(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
        } finally {
            setLoading(false);
        }
    };

    const createUser = async (userData: UserFormData) => {
        try {
            setLoading(true);
            const response = await fetch('/api/users', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(userData),
            });
            if (!response.ok) {
                throw new Error('Failed to create user');
            }
            const newUser = await response.json();
            setUsers(prev => [...prev, newUser]);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const updateUser = async (id: string, userData: Partial<UserFormData>) => {
        try {
            setLoading(true);
            const response = await fetch(`/api/users/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(userData),
            });
            if (!response.ok) {
                throw new Error('Failed to update user');
            }
            const updatedUser = await response.json();
            setUsers(prev => prev.map(user => 
                user.id === id ? updatedUser : user
            ));
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const deleteUser = async (id: string) => {
        try {
            setLoading(true);
            const response = await fetch(`/api/users/${id}`, {
                method: 'DELETE',
            });
            if (!response.ok) {
                throw new Error('Failed to delete user');
            }
            setUsers(prev => prev.filter(user => user.id !== id));
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const getUser = async (id: string): Promise<User> => {
        try {
            setLoading(true);
            const response = await fetch(`/api/users/${id}`);
            if (!response.ok) {
                throw new Error('Failed to fetch user');
            }
            return await response.json();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
            throw err;
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, []);

    return {
        users,
        loading,
        error,
        createUser,
        updateUser,
        deleteUser,
        getUser
    };
}; 