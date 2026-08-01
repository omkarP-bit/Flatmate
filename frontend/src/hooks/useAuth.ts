import { useAuthStore } from '../store/authStore';
import { userApi } from '../api/userApi';
import { supabase } from '../lib/supabase';

export function useAuth() {
  const { user, token, isAuthenticated, setUser, clearAuth } = useAuthStore();

  const refreshUser = async () => {
    try {
      const updated = await userApi.getMe();
      setUser(updated);
      return updated;
    } catch {
      return null;
    }
  };

  const signOut = async () => {
    await supabase.auth.signOut();
    clearAuth();
  };

  return { user, token, isAuthenticated, refreshUser, signOut };
}
