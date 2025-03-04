import { User } from '../types/user';
import { api } from './api';

export class AuthService {
  static async login(username: string, password: string): Promise<User> {
    const response = await api.post('/auth/login', {
      username,
      password
    });
    
    const { access_token, user } = response.data;
    
    // Store token
    localStorage.setItem('token', access_token);
    
    return user;
  }
  
  static async logout(): Promise<void> {
    try {
      await api.post('/auth/logout');
    } finally {
      localStorage.removeItem('token');
    }
  }
  
  static async checkAuth(): Promise<User> {
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token found');
    }
    
    const response = await api.get('/auth/me');
    return response.data;
  }
} 