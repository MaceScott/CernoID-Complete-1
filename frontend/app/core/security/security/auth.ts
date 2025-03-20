import axios from 'axios';

// Use a more flexible backend URL configuration
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || process.env.BACKEND_URL || 'http://localhost:8000';

interface User {
  id: string;
  email: string;
  username: string;
  role: string;
  permissions: string[];
  is_active: boolean;
  last_login: string;
}

interface Tokens {
  access_token: string;
  refresh_token: string;
}

class AuthService {
  async authenticate_user(email: string, password: string): Promise<User | null> {
    try {
      const response = await axios.post(`${BACKEND_URL}/api/auth/login`, {
        email,
        password,
      });
      return response.data.user;
    } catch (error) {
      console.error('Authentication error:', error);
      return null;
    }
  }

  async create_tokens(user: User): Promise<Tokens> {
    try {
      const response = await axios.post(`${BACKEND_URL}/api/auth/tokens`, {
        user_id: user.id,
      });
      return response.data;
    } catch (error) {
      console.error('Token creation error:', error);
      throw new Error('Failed to create tokens');
    }
  }

  async verify_token(token: string): Promise<boolean> {
    try {
      await axios.post(`${BACKEND_URL}/api/auth/verify`, {
        token,
      });
      return true;
    } catch (error) {
      return false;
    }
  }

  async refresh_token(refresh_token: string): Promise<Tokens | null> {
    try {
      const response = await axios.post(`${BACKEND_URL}/api/auth/refresh`, {
        refresh_token,
      });
      return response.data;
    } catch (error) {
      return null;
    }
  }
}

export const auth_service = new AuthService(); 