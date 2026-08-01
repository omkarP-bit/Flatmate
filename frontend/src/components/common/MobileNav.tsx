import React from 'react';
import { useRoomStore } from '../../store/roomStore';
import type { Theme } from '../../hooks/useTheme';

type Page = 'dashboard' | 'expenses' | 'payments' | 'history' | 'profile' | 'room';

interface MobileNavProps {
  activePage: Page;
  onNavigate: (page: Page) => void;
  theme: Theme;
  onToggleTheme: () => void;
}

const ROOM_COLORS = ['#ccff00','#7F77DD','#EF9F27','#378ADD','#639922'];

const ITEMS: Array<{ id: Page; label: string; icon: React.ReactNode }> = [
  {
    id: 'dashboard',
    label: 'Home',
    icon: <svg width="20" height="20" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6"><rect x="1" y="1" width="6" height="6" rx="1.5"/><rect x="9" y="1" width="6" height="6" rx="1.5"/><rect x="1" y="9" width="6" height="6" rx="1.5"/><rect x="9" y="9" width="6" height="6" rx="1.5"/></svg>,
  },
  {
    id: 'expenses',
    label: 'Expenses',
    icon: <svg width="20" height="20" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6"><path d="M2 5h12M2 8h8M2 11h5"/></svg>,
  },
  {
    id: 'payments',
    label: 'Pay',
    icon: <svg width="20" height="20" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6"><path d="M8 2v12M3 7l5-5 5 5"/></svg>,
  },
  {
    id: 'room',
    label: 'Room',
    icon: <svg width="20" height="20" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6"><path d="M2 7l6-4 6 4v6a1 1 0 0 1-1 1h-4v-4H7v4H3a1 1 0 0 1-1-1V7z"/></svg>,
  },
  {
    id: 'profile',
    label: 'Profile',
    icon: <svg width="20" height="20" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6"><circle cx="8" cy="5" r="3"/><path d="M2.5 14c.8-2.5 3-4 5.5-4s4.7 1.5 5.5 4"/></svg>,
  },
];

export default function MobileNav({ activePage, onNavigate, theme, onToggleTheme }: MobileNavProps) {
  const { rooms, activeRoomId, setActiveRoom } = useRoomStore();

  return (
    <nav className="fm-mobile-nav">
      {rooms.length > 1 && (
        <div className="fm-mobile-rooms">
          {rooms.map((room, i) => (
            <button
              key={room.id}
              className={`fm-mobile-room${activeRoomId === room.id ? ' active' : ''}`}
              onClick={() => setActiveRoom(room.id)}
            >
              <span className="dot" style={{ background: ROOM_COLORS[i % ROOM_COLORS.length] }} />
              {room.name}
            </button>
          ))}
        </div>
      )}
      <div className="fm-mobile-nav-inner">
        {ITEMS.map(item => (
          <button
            key={item.id}
            className={`fm-mobile-nav-item${activePage === item.id ? ' active' : ''}`}
            onClick={() => onNavigate(item.id)}
          >
            <span className="ico">{item.icon}</span>
            {item.label}
          </button>
        ))}
        <button
          className="fm-mobile-nav-item"
          onClick={onToggleTheme}
          aria-label="Toggle theme"
        >
          <span className="ico">
            {theme === 'dark' ? (
              <svg width="20" height="20" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6"><circle cx="8" cy="8" r="3"/><path d="M8 1v2M8 13v2M1 8h2M13 8h2M3 3l1.5 1.5M11.5 11.5L13 13M13 3l-1.5 1.5M4.5 11.5L3 13"/></svg>
            ) : (
              <svg width="20" height="20" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6"><path d="M13 9.5A5.5 5.5 0 0 1 6.5 3a5.5 5.5 0 1 0 6.5 6.5z"/></svg>
            )}
          </span>
        </button>
      </div>
    </nav>
  );
}
