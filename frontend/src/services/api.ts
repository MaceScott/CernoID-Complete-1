import axios from 'axios';
import { toast } from 'react-toastify';

// Create axios instance with default config
export const api = axios.create({
    baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api',
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json'
    }
});

// Request interceptor
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor
api.interceptors.response.use(
    (response) => {
        return response;
    },
    async (error) => {
        const originalRequest = error.config;

        // Handle token refresh
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
                const refreshToken = localStorage.getItem('refreshToken');
                if (!refreshToken) {
                    throw new Error('No refresh token');
                }

                const response = await api.post('/auth/refresh', {
                    refresh_token: refreshToken
                });

                const { access_token } = response.data;
                localStorage.setItem('token', access_token);

                originalRequest.headers.Authorization = `Bearer ${access_token}`;
                return api(originalRequest);
            } catch (refreshError) {
                // Clear tokens and redirect to login
                localStorage.removeItem('token');
                localStorage.removeItem('refreshToken');
                window.location.href = '/login';
                return Promise.reject(refreshError);
            }
        }

        // Handle other errors
        const errorMessage = error.response?.data?.message || 
            'An unexpected error occurred';
            
        // Show error toast
        toast.error(errorMessage, {
            position: 'top-right',
            autoClose: 5000,
            hideProgressBar: false,
            closeOnClick: true,
            pauseOnHover: true,
            draggable: true
        });

        return Promise.reject(error);
    }
);

// API service methods
export const apiService = {
    // Auth
    login: (username: string, password: string) => 
        api.post('/auth/login', { username, password }),
    logout: () => 
        api.post('/auth/logout'),
    refreshToken: (refreshToken: string) => 
        api.post('/auth/refresh', { refresh_token: refreshToken }),
    
    // Recognition
    processImage: (imageData: string) => 
        api.post('/recognition/process', { image: imageData }),
    getResults: (resultId: string) => 
        api.get(`/recognition/results/${resultId}`),
    
    // Users
    getUsers: (params?: any) => 
        api.get('/users', { params }),
    createUser: (userData: any) => 
        api.post('/users', userData),
    updateUser: (userId: number, userData: any) => 
        api.put(`/users/${userId}`, userData),
    deleteUser: (userId: number) => 
        api.delete(`/users/${userId}`),
    
    // Settings
    getSettings: () => 
        api.get('/settings'),
    updateSettings: (settings: any) => 
        api.put('/settings', settings),
    resetSettings: () => 
        api.post('/settings/reset')
}; 