import { useEffect, useState } from 'react';
import React from 'react';
import './App.css';
import { useAuthStore } from './store/authStore';
import { useRoomStore } from './store/roomStore';
import { useExpenseStore } from './store/expenseStore';
import { useTheme } from './hooks/useTheme';
import { supabase } from './lib/supabase';
import { finalizeSession } from './lib/authFlow';

import Sidebar from './components/common/Sidebar';
import MobileNav from './components/common/MobileNav';
import Login from './pages/Login';
import Callback from './pages/Callback';
import Dashboard from './pages/Dashboard';
import Expenses from './pages/Expenses';
import Payments from './pages/Payments';
import Profile from './pages/Profile';
import Room from './pages/Room';

type Page = 'dashboard' | 'expenses' | 'payments' | 'history' | 'profile' | 'room';

function getInitialPage(): string {
  const path = window.location.pathname;
  if (path === '/callback') return 'callback';
  if (path === '/login')    return 'login';
  return 'dashboard';
}

export default function App() {
  const { isAuthenticated, setToken, setUser, setAuthError, setAuthStatus } = useAuthStore();
  const { fetchMyRooms, activeRoomId } = useRoomStore();
  const { fetchExpenses, fetchMyBalance, fetchSuggestions } = useExpenseStore();
  const { theme, toggleTheme } = useTheme();

  const [page, setPage] = useState<string>(getInitialPage);

  // If the session exists but the store isn't hydrated yet (e.g. cold start),
  // recover it from Supabase's persisted storage.
  useEffect(() => {
    if (isAuthenticated) return;
    supabase.auth.getSession().then(async ({ data, error }) => {
      if (error) {
        console.error('[auth] getSession failed:', error);
        setAuthError(error.message);
        return;
      }
      if (data.session) {
        console.log('[auth] restored persisted session');
        setAuthStatus('Restoring session…');
        await finalizeSession(data.session.access_token, setToken, setUser);
        setAuthStatus(null);
      }
    });
  }, []);

  // On auth → load rooms
  useEffect(() => {
    if (isAuthenticated) {
      fetchMyRooms();
    }
  }, [isAuthenticated]);

  // On active room change → load expenses + balance
  useEffect(() => {
    if (activeRoomId) {
      fetchExpenses(activeRoomId);
      fetchMyBalance(activeRoomId);
      fetchSuggestions(activeRoomId);
    }
  }, [activeRoomId]);

  // Unauthenticated routes
  if (page === 'callback') return <Callback onSuccess={() => setPage('dashboard')} />;
  if (!isAuthenticated)    return <Login />;

  const renderPage = () => {
    switch (page as Page) {
      case 'dashboard': return <Dashboard onNavigate={p => setPage(p)} />;
      case 'expenses':  return <Expenses />;
      case 'payments':  return <Payments />;
      case 'profile':   return <Profile />;
      case 'room':      return <Room />;
      default:          return <Dashboard onNavigate={p => setPage(p)} />;
    }
  };

  return (
    <div className="fm-app">
      <Sidebar activePage={page as Page} onNavigate={p => setPage(p)} theme={theme} onToggleTheme={toggleTheme} />
      <div className="fm-main">
        {renderPage()}
      </div>
      <MobileNav activePage={page as Page} onNavigate={p => setPage(p)} theme={theme} onToggleTheme={toggleTheme} />
    </div>
  );
}

