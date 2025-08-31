import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Type definitions
interface UserProfile {
  first_name?: string;
  last_name?: string;
  company?: string;
  job_title?: string;
  phone?: string;
  bio?: string;
  avatar_url?: string;
}

interface User {
  id: string;
  email: string;
  username: string;
  profile?: UserProfile;
  notes_count?: number;
  total_time_saved?: number;
  created_at: string;
  last_login?: string;
}

interface LoginResponse {
  access_token: string;
  user: User;
}

interface RegisterData {
  email: string;
  username: string;
  password: string;
  first_name: string;
  last_name: string;
  profession: string;
  industry: string;
  interests: string;
}

interface AuthResult {
  success: boolean;
  error?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<AuthResult>;
  register: (userData: RegisterData) => Promise<AuthResult>;
  logout: () => void;
  updateProfile: (profileData: Partial<UserProfile>) => Promise<AuthResult>;
  isAuthenticated: boolean;
}

interface AuthProviderProps {
  children: ReactNode;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('auto_me_token'));
  const [loading, setLoading] = useState<boolean>(true);

  // Set up axios interceptors
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [token]);

  // Load user profile on startup
  useEffect(() => {
    const loadUser = async () => {
      if (token) {
        try {
          const response = await axios.get<User>(`${API}/auth/me`);
          setUser(response.data);
        } catch (error) {
          // Token invalid, clear it
          localStorage.removeItem('auto_me_token');
          setToken(null);
          delete axios.defaults.headers.common['Authorization'];
        }
      }
      setLoading(false);
    };

    loadUser();
  }, [token]);

  const login = async (email: string, password: string): Promise<AuthResult> => {
    try {
      const response = await axios.post<LoginResponse>(`${API}/auth/login`, {
        email,
        password
      });
      
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('auto_me_token', access_token);
      setToken(access_token);
      setUser(userData);
      
      return { success: true };
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Login failed';
      const errorText = typeof errorMessage === 'string' 
        ? errorMessage 
        : Array.isArray(errorMessage) 
          ? errorMessage.map((err: any) => err.msg || 'Validation error').join(', ')
          : 'Login failed';
      
      return { 
        success: false, 
        error: errorText
      };
    }
  };

  const register = async (userData: RegisterData): Promise<AuthResult> => {
    try {
      const response = await axios.post<LoginResponse>(`${API}/auth/register`, userData);
      
      const { access_token, user: newUser } = response.data;
      
      localStorage.setItem('auto_me_token', access_token);
      setToken(access_token);
      setUser(newUser);
      
      return { success: true };
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Registration failed';
      const errorText = typeof errorMessage === 'string' 
        ? errorMessage 
        : Array.isArray(errorMessage) 
          ? errorMessage.map((err: any) => err.msg || 'Validation error').join(', ')
          : 'Registration failed';
      
      return { 
        success: false, 
        error: errorText
      };
    }
  };

  const logout = (): void => {
    localStorage.removeItem('auto_me_token');
    setToken(null);
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
  };

  const updateProfile = async (profileData: Partial<UserProfile>): Promise<AuthResult> => {
    try {
      const response = await axios.put<User>(`${API}/auth/me`, profileData);
      setUser(response.data);
      return { success: true };
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Profile update failed';
      const errorText = typeof errorMessage === 'string' 
        ? errorMessage 
        : Array.isArray(errorMessage) 
          ? errorMessage.map((err: any) => err.msg || 'Validation error').join(', ')
          : 'Profile update failed';
      
      return { 
        success: false, 
        error: errorText
      };
    }
  };

  const value: AuthContextType = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    updateProfile,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};