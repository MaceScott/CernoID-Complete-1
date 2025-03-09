import { type LoginCredentials, type RegisterData, type AuthResponse, type ApiResponse } from './types';

const API_BASE = '/api/auth';

export async function login(credentials: LoginCredentials): Promise<ApiResponse<AuthResponse>> {
  const response = await fetch(`${API_BASE}/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(credentials),
  });

  return response.json();
}

export async function register(data: RegisterData): Promise<ApiResponse<AuthResponse>> {
  const response = await fetch(`${API_BASE}/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  return response.json();
}

export async function logout(): Promise<ApiResponse<void>> {
  const response = await fetch(`${API_BASE}/logout`, {
    method: 'POST',
  });

  return response.json();
}

export async function getCurrentUser(): Promise<ApiResponse<AuthResponse>> {
  const response = await fetch(`${API_BASE}/me`, {
    method: 'GET',
  });

  return response.json();
}

export async function refreshToken(): Promise<ApiResponse<{ token: string }>> {
  const response = await fetch(`${API_BASE}/refresh`, {
    method: 'POST',
  });

  return response.json();
}

export async function resetPassword(email: string): Promise<ApiResponse<void>> {
  const response = await fetch(`${API_BASE}/reset-password`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email }),
  });

  return response.json();
}

export async function updatePassword(
  token: string,
  password: string,
  confirmPassword: string
): Promise<ApiResponse<void>> {
  const response = await fetch(`${API_BASE}/update-password`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ token, password, confirmPassword }),
  });

  return response.json();
} 