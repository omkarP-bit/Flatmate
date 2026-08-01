import { useEffect, useRef, useState } from 'react';
import React from 'react';
import { useRoomStore } from '../../store/roomStore';

const ROOM_COLORS = ['#ccff00','#7F77DD','#EF9F27','#378ADD','#639922'];

export default function RoomSwitcher({ onNavigate }: { onNavigate?: (page: string) => void }) {
  const { rooms, activeRoomId, setActiveRoom } = useRoomStore();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const activeRoom = rooms.find(r => r.id === activeRoomId);

  useEffect(() => {
    const onDocClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', onDocClick);
    return () => document.removeEventListener('mousedown', onDocClick);
  }, []);

  return (
    <div className="fm-room-switcher" ref={ref}>
      <button
        className="fm-room-switcher-toggle"
        onClick={() => setOpen(o => !o)}
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        {activeRoom && (
          <span
            className="dot"
            style={{ background: ROOM_COLORS[(rooms.findIndex(r => r.id === activeRoomId) % ROOM_COLORS.length)] }}
          />
        )}
        <span className="name">{activeRoom?.name ?? 'My flat'}</span>
        <svg width="10" height="10" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5"
          style={{ transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 0.15s ease' }}>
          <path d="M2 4l4 4 4-4" />
        </svg>
      </button>

      {open && (
        <div className="fm-room-switcher-menu" role="listbox">
          {rooms.length === 0 && (
            <div className="fm-room-switcher-empty">No rooms yet</div>
          )}
          {rooms.map((room, i) => (
            <button
              key={room.id}
              className={`fm-room-switcher-item${activeRoomId === room.id ? ' active' : ''}`}
              onClick={() => { setActiveRoom(room.id); setOpen(false); }}
            >
              <span className="dot" style={{ background: ROOM_COLORS[i % ROOM_COLORS.length] }} />
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{room.name}</span>
              {activeRoomId === room.id && (
                <svg width="11" height="11" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.6"
                  style={{ marginLeft: 'auto', flexShrink: 0 }}>
                  <path d="M2 6.5l2.5 2.5L10 3.5" />
                </svg>
              )}
            </button>
          ))}
          <button
            className="fm-room-switcher-item add"
            onClick={() => { setOpen(false); onNavigate?.('room'); }}
          >
            <span className="dot" style={{ border: '1px dashed var(--border-mid)', background: 'transparent' }} />
            Join or create room
          </button>
        </div>
      )}
    </div>
  );
}
