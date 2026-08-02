import { useEffect, useRef } from 'react';
import { useAuthStore } from '../store/authStore';
import { supabase } from '../lib/supabase';
import { finalizeSession } from '../lib/authFlow';
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

      await finalizeSession(session.access_token, setToken, setUser);
      // Clean the URL so a later cold start doesn't re-enter the callback route.
      window.history.replaceState({}, document.title, window.location.pathname);
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
