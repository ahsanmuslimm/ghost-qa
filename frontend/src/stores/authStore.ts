import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { decodeToken, isTokenExpired, permissionsForRole } from '../lib/jwt';

export interface AuthUser {
  email: string;
  role: string;
  permissions: string[];
}

interface AuthState {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (token: string) => void;
  logout: () => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  hasPermission: (permission: string) => boolean;
}

function userFromToken(token: string): AuthUser | null {
  const payload = decodeToken(token);
  if (!payload) return null;
  return {
    email: payload.sub,
    role: payload.role,
    permissions: permissionsForRole(payload.role),
  };
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      login: (token) => {
        localStorage.setItem('token', token);
        set({
          user: userFromToken(token),
          token,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        });
      },
      logout: () => {
        localStorage.removeItem('token');
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
        });
      },
      setLoading: (isLoading) => set({ isLoading }),
      setError: (error) => set({ error, isLoading: false }),
      hasPermission: (permission) => {
        const { user, token } = get();
        if (!user || !token || isTokenExpired(token)) return false;
        return user.permissions.includes(permission);
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated && !!state.token && !isTokenExpired(state.token),
      }),
    }
  )
);
