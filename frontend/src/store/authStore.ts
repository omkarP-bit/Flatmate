import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User } from '../types/user.types';

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  authError: string | null;
  authStatus: string | null;
  setToken: (token: string) => void;
  setUser: (user: User) => void;
  setAuthError: (message: string | null) => void;
  setAuthStatus: (message: string | null) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      authError: null,
      authStatus: null,

      setToken: (token) => set({ token, isAuthenticated: true }),

      setUser: (user) => set({ user }),

      setAuthError: (authError) => set({ authError }),

      setAuthStatus: (authStatus) => set({ authStatus }),

      clearAuth: () => set({ token: null, user: null, isAuthenticated: false, authError: null, authStatus: null }),
    }),
    { name: 'flatmate-auth' }
  )
);
