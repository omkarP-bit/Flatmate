import { useEffect, useState } from 'react';
import { useRoom } from '../hooks/useRoom';
import MemberCard from '../components/room/MemberCard';
import Button from '../components/common/Button';
import Loader from '../components/common/Loader';
import { useToast } from '../components/common/Toast';
import { useConfirm } from '../components/common/Confirm';

type Tab = 'settings' | 'join' | 'create';

export default function Room() {
  const { activeRoom, members, isAdmin, loading, handleCreate, handleJoin, handleRemoveMember, handleUpdateRoom, handleRegenerateCode, handleLeave: handleLeaveRoom } = useRoom();
  const toast = useToast();
  const { confirm } = useConfirm();
  const [tab,       setTab]       = useState<Tab>('settings');
  const [roomName,  setRoomName]  = useState(activeRoom?.name ?? '');
  const [address,   setAddress]   = useState(activeRoom?.address ?? '');
  const [joinCode,  setJoinCode]  = useState('');
  const [newName,   setNewName]   = useState('');
  const [newAddr,   setNewAddr]   = useState('');
  const [saving,    setSaving]    = useState(false);
  const [error,     setError]     = useState('');
  const [copied,    setCopied]    = useState(false);

  useEffect(() => {
    setRoomName(activeRoom?.name ?? '');
    setAddress(activeRoom?.address ?? '');
  }, [activeRoom?.id]);

  const handleJoinSubmit = async () => {
    if (!joinCode.trim()) return setError('Enter a room code');
    setSaving(true); setError('');
    try { await handleJoin(joinCode.trim()); setJoinCode(''); toast.success('Joined room!'); }
    catch (e: any) { const msg = e.response?.data?.detail ?? 'Room not found'; setError(msg); toast.error(msg); }
    finally { setSaving(false); }
  };

  const handleCreateSubmit = async () => {
    if (!newName.trim()) return setError('Enter a room name');
    setSaving(true); setError('');
    try { await handleCreate(newName.trim(), newAddr.trim() || undefined); setNewName(''); setNewAddr(''); toast.success('Room created!'); }
    catch (e: any) { const msg = e.response?.data?.detail ?? 'Failed to create room'; setError(msg); toast.error(msg); }
    finally { setSaving(false); }
  };

  const copyCode = () => {
    if (activeRoom?.room_code) {
      navigator.clipboard.writeText(activeRoom.room_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      toast.success('Invite code copied');
    }
  };

  const handleSave = async () => {
    if (!roomName.trim()) return toast.error('Room name is required');
    setSaving(true);
    try {
      await handleUpdateRoom({ name: roomName.trim(), address: address.trim() || undefined });
      toast.success('Room details saved');
    } catch (e: any) {
      toast.error(e.response?.data?.detail ?? 'Failed to save room');
    } finally {
      setSaving(false);
    }
  };

  const handleRegenerate = async () => {
    try {
      await handleRegenerateCode();
      toast.success('Invite code regenerated');
    } catch (e: any) {
      toast.error(e.response?.data?.detail ?? 'Failed to regenerate code');
    }
  };

  const handleRemove = async (uid: string) => {
    const ok = await confirm({
      title: 'Remove member?',
      message: 'This removes them from the room and their shares.',
      confirmLabel: 'Remove',
      danger: true,
    });
    if (!ok) return;
    try {
      await handleRemoveMember(uid);
      toast.success('Member removed');
    } catch (e: any) {
      toast.error(e.response?.data?.detail ?? 'Failed to remove member');
    }
  };

  const handleLeave = async () => {
    const ok = await confirm({
      title: 'Leave this room?',
      message: 'Leaving removes you from all expense splits. Settled amounts are unaffected.',
      confirmLabel: 'Leave',
      danger: true,
    });
    if (!ok) return;
    try {
      await handleLeaveRoom();
      toast.success('You left the room');
    } catch (e: any) {
      toast.error(e.response?.data?.detail ?? 'Failed to leave room');
    }
  };

  return (
    <div className="fm-page">
      <header className="fm-topbar">
        <div style={s.topLeft}>
          <span style={s.breadcrumb}>{activeRoom?.name ?? 'Room'}</span>
          <span style={s.sep}>/</span>
          <span style={s.pageTitle}>Room settings</span>
        </div>
      </header>

      {/* Tab nav */}
      <div style={s.tabNav}>
        {(['settings','join','create'] as Tab[]).map(t => (
          <button key={t} onClick={() => { setTab(t); setError(''); }}
            style={{ ...s.tab, ...(tab === t ? s.tabActive : {}) }}>
            {t === 'settings' ? 'Settings' : t === 'join' ? 'Join a room' : 'Create room'}
          </button>
        ))}
      </div>

      <div className="fm-content">
        {loading && <Loader />}

        {/* Settings tab */}
        {tab === 'settings' && activeRoom && (
          <div className="fm-two-col">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.1rem' }}>

              {/* Room details */}
              <div className="fm-card">
                <div style={s.cardTitle}>Room details</div>
                <div style={s.field}>
                  <label style={s.label}>Room name</label>
                  <input style={s.input} value={roomName} onChange={e => setRoomName(e.target.value)} />
                </div>
                <div style={s.field}>
                  <label style={s.label}>Address</label>
                  <textarea rows={2} style={s.textarea} value={address} onChange={e => setAddress(e.target.value)} />
                </div>
                <div style={s.btnRow}>
                  <Button variant="primary" size="sm" loading={saving} onClick={handleSave}>Save</Button>
                  <Button variant="ghost" size="sm" onClick={() => { setRoomName(activeRoom?.name ?? ''); setAddress(activeRoom?.address ?? ''); }}>Cancel</Button>
                </div>
              </div>

              {/* Members */}
              <div className="fm-card">
                <div style={s.cardHeader}>
                  <span style={s.cardTitle}>Members ({members.length})</span>
                  <Button variant="ghost" size="sm" onClick={() => { if (activeRoom?.room_code) copyCode(); }}>+ Invite</Button>
                </div>
                {members.map(m => (
                  <MemberCard key={m.user_id} member={m}
                    isRequesterAdmin={isAdmin}
                    onRemove={isAdmin ? handleRemove : undefined} />
                ))}
              </div>

            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.1rem' }}>

              {/* Stats */}
              <div className="fm-card">
                <div style={s.cardTitle}>Room stats</div>
                <div style={s.statsGrid}>
                  {[
                    { label: 'Members',      value: String(members.length) },
                    { label: 'Active since', value: activeRoom ? new Date(activeRoom.created_at).toLocaleDateString('en-IN', { month: 'short', year: 'numeric' }) : '—' },
                  ].map(st => (
                    <div key={st.label} style={s.statCell}>
                      <div style={s.statLabel}>{st.label}</div>
                      <div style={s.statVal}>{st.value}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Invite code */}
              <div className="fm-card">
                <div style={s.cardTitle}>Invite code</div>
                <div style={s.inviteCard}>
                  <div style={s.inviteHint}>Share this code to invite flatmates</div>
                  <div style={s.inviteCode}>{activeRoom.room_code}</div>
                  <div style={s.inviteMeta}>Anyone with this code can join</div>
                </div>
                <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
                  <Button variant="primary" style={{ flex: 1 }} onClick={copyCode}>
                    {copied ? 'Copied!' : 'Copy code'}
                  </Button>
                  <Button variant="ghost" onClick={handleRegenerate}>Regenerate</Button>
                </div>
              </div>

              {/* Danger */}
              <div style={s.dangerZone}>
                <div style={s.dzTitle}>Danger zone</div>
                <div style={s.dzDesc}>Leaving removes you from all expense splits. Settled amounts are unaffected.</div>
                <Button variant="danger" size="sm" onClick={handleLeave}>Leave this room</Button>
              </div>

            </div>
          </div>
        )}

        {/* Join tab */}
        {tab === 'join' && (
          <div style={{ maxWidth: 400, width: '100%' }}>
            <div className="fm-card">
              <div style={s.cardTitle}>Join a room</div>
              <p style={s.cardDesc}>Enter the invite code shared by your flatmate. Codes are 8 characters, uppercase.</p>
              <div style={s.field}>
                <label style={s.label}>Room code</label>
                <input style={{ ...s.input, fontFamily: 'var(--font-mono)', letterSpacing: '0.1em', fontSize: 16 }}
                  placeholder="K7XQ2WRP"
                  value={joinCode}
                  onChange={e => setJoinCode(e.target.value.toUpperCase())}
                  maxLength={8} />
              </div>
              {error && <div style={s.errorMsg}>{error}</div>}
              <div style={{ marginTop: '0.85rem' }}>
                <Button variant="primary" loading={saving} onClick={handleJoinSubmit}>Join room</Button>
              </div>
            </div>
          </div>
        )}

        {/* Create tab */}
        {tab === 'create' && (
          <div style={{ maxWidth: 400, width: '100%' }}>
            <div className="fm-card">
              <div style={s.cardTitle}>Create a new room</div>
              <p style={s.cardDesc}>You'll be the admin. Share the invite code with flatmates after creating.</p>
              <div style={s.field}>
                <label style={s.label}>Room name</label>
                <input style={s.input} placeholder="e.g. Mumbai Flat 4B" value={newName} onChange={e => setNewName(e.target.value)} />
              </div>
              <div style={s.field}>
                <label style={s.label}>Address (optional)</label>
                <textarea rows={2} style={s.textarea} placeholder="Full address…" value={newAddr} onChange={e => setNewAddr(e.target.value)} />
              </div>
              {error && <div style={s.errorMsg}>{error}</div>}
              <div style={{ marginTop: '0.85rem' }}>
                <Button variant="primary" loading={saving} onClick={handleCreateSubmit}>Create room</Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  topLeft:    { display: 'flex', alignItems: 'center', gap: 10 },
  breadcrumb: { fontSize: 13, color: 'var(--text-tertiary)' },
  sep:        { color: 'var(--border-mid)' },
  pageTitle:  { fontSize: 15, fontWeight: 500 },
  tabNav:     { display: 'flex', padding: '0 1.5rem', gap: 0, borderBottom: '0.5px solid var(--border-light)', background: 'var(--bg-primary)', overflowX: 'auto', flexShrink: 0 },
  tab:        { padding: '0.65rem 1rem', fontSize: 13, cursor: 'pointer', color: 'var(--text-secondary)', background: 'transparent', border: 'none', borderBottom: '2px solid transparent', marginBottom: -1, fontFamily: 'var(--font-sans)', whiteSpace: 'nowrap' },
  tabActive:  { color: 'var(--text-primary)', borderBottomColor: '#ccff00', fontWeight: 500 },
  cardHeader: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.85rem', gap: 8 },
  cardTitle:  { fontSize: 13.5, fontWeight: 600, marginBottom: '0.85rem' },
  cardDesc:   { fontSize: 12, color: 'var(--text-tertiary)', lineHeight: 1.5, marginBottom: '0.85rem' },
  field:      { display: 'flex', flexDirection: 'column', gap: 5, marginBottom: '0.75rem' },
  label:      { fontSize: 12, color: 'var(--text-secondary)', fontWeight: 500 },
  input:      { height: 34, padding: '0 10px', borderRadius: 'var(--r-md)', border: '0.5px solid var(--border-mid)', background: 'var(--bg-primary)', color: 'var(--text-primary)', fontSize: 13, fontFamily: 'var(--font-sans)', outline: 'none', width: '100%' },
  textarea:   { padding: '8px 10px', borderRadius: 'var(--r-md)', border: '0.5px solid var(--border-mid)', background: 'var(--bg-primary)', color: 'var(--text-primary)', fontSize: 13, fontFamily: 'var(--font-sans)', outline: 'none', width: '100%', resize: 'none' },
  btnRow:     { display: 'flex', gap: 8 },
  statsGrid:  { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 },
  statCell:   { background: 'var(--bg-secondary)', borderRadius: 'var(--r-md)', padding: '0.75rem' },
  statLabel:  { fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 3 },
  statVal:    { fontSize: 18, fontWeight: 500 },
  inviteCard: { background: 'var(--bg-secondary)', borderRadius: 'var(--r-md)', padding: '0.85rem 1rem' },
  inviteHint: { fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 6 },
  inviteCode: { fontFamily: 'var(--font-mono)', fontSize: 20, fontWeight: 500, letterSpacing: '0.15em', color: 'var(--text-primary)' },
  inviteMeta: { fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 },
  dangerZone: { border: '0.5px solid var(--danger-border)', borderRadius: 'var(--r-lg)', padding: '1.25rem', background: 'var(--bg-danger)' },
  dzTitle:    { fontSize: 14, fontWeight: 500, color: 'var(--text-danger)', marginBottom: 5 },
  dzDesc:     { fontSize: 12, color: 'var(--text-danger)', opacity: 0.75, lineHeight: 1.5, marginBottom: '0.85rem' },
  errorMsg:   { fontSize: 12, color: 'var(--text-danger)', background: 'var(--bg-danger)', padding: '8px 12px', borderRadius: 'var(--r-md)', marginTop: 4 },
};

import React from 'react';