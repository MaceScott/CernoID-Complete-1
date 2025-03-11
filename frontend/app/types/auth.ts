export interface User {
  id: string;
  email: string;
  role: string;
  permissions: string[];
  zones: string[];
}

export interface LoginData {
  email: string;
  password: string;
}

export interface RegisterData extends LoginData {
  role?: string;
}

export interface AuthResponse {
  user: User;
  token: string;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface AuthContextType extends AuthState {
  login: (credentials: LoginData) => Promise<void>;
  loginWithFace: (imageData: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  resetPassword: (email: string) => Promise<void>;
  updatePassword: (token: string, password: string, confirmPassword: string) => Promise<void>;
} 