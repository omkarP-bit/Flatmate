import { useEffect, useRef } from 'react';
import { useAuthStore } from '../store/authStore';
import { supabase } from '../lib/supabase';
import { userApi } from '../api/userApi';
import Loader from '../components/common/Loader';

interface CallbackProps {
  onSuccess: () => void;
}

export default function Callback({ onSuccess }: CallbackProps) {
  const { setToken, setUser } = useAuthStore();
  const called = useRef(false);

  useEffect(() => {
    if (called.current) return;
    called.current = true;

    handleCallback();
  }, []);

  const handleCallback = async () => {
    try {
      const code = new URLSearchParams(window.location.search).get('code');

      let session;
      if (code) {
        console.log('[auth] PKCE code detected, exchanging…');
        const { data, error } = await supabase.auth.exchangeCodeForSession(code);
        if (error) throw error;
        session = data.session;
      } else {
        console.log('[auth] checking session from URL fragment…', window.location.href);
        const { data, error } = await supabase.auth.getSession();
        if (error) throw error;
        session = data.session;
      }

      if (!session) {
        console.error('[auth] no session found on callback URL', window.location.href);
        window.location.href = '/login';
        return;
      }

      const accessToken = session.access_token;
      setToken(accessToken);

      const payload = JSON.parse(atob(accessToken.split('.')[1]));
      const user = await userApi.createOrGet({
        name: payload.user_metadata?.full_name ?? payload.email,
        email: payload.email,
      });
      setUser(user);

      onSuccess();
    } catch (err) {
      console.error('[auth] callback failed:', err);
      window.location.href = '/login';
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
        <Loader size={32} />
        <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>Signing you in…</p>
      </div>
    </div>
  );
}
