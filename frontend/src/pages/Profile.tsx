import { useRef, useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { userApi } from '../api/userApi';
import { useRoomStore } from '../store/roomStore';
import Avatar from '../components/common/Avatar';
import Button from '../components/common/Button';
import { useToast } from '../components/common/Toast';
import { useConfirm } from '../components/common/Confirm';

type Section = 'profile' | 'notifications' | 'payment';

const NAV: Array<{ id: Section; label: string }> = [
  { id: 'profile',       label: 'Profile' },
  { id: 'notifications', label: 'Notifications' },
  { id: 'payment',       label: 'Payment info' },
];

export default function Profile() {
  const { user, refreshUser, signOut } = useAuth();
  const { activeRoomId, fetchMembers } = useRoomStore();
  const toast = useToast();
  const { confirm } = useConfirm();
  const [active,  setActive]  = useState<Section>('profile');
  const [name,    setName]    = useState(user?.name ?? '');
  const [phone,   setPhone]   = useState(user?.phone ?? '');
  const [upi,     setUpi]     = useState(user?.upi_id ?? '');
  const [saving,  setSaving]  = useState(false);
  const [saved,   setSaved]   = useState(false);
  const [uploading, setUploading] = useState(false);
  const [notifs,  setNotifs]  = useState({ newExpense: true, paymentReceived: true, smartReminders: true, weekly: false });
  const fileRef = useRef<HTMLInputElement>(null);

  const saveProfile = async () => {
    setSaving(true);
    try {
      await userApi.updateMe({ name, phone, upi_id: upi });
      await refreshUser();
      if (activeRoomId) await fetchMembers(activeRoomId);
      setSaved(true);
      toast.success('Profile saved');
      setTimeout(() => setSaved(false), 2000);
    } catch (e: any) {
      toast.error(e.response?.data?.detail ?? 'Failed to save profile');
    } finally {
      setSaving(false);
    }
  };

  const saveUpi = async () => {
    setSaving(true);
    try {
      await userApi.updateMe({ upi_id: upi });
      await refreshUser();
      toast.success('UPI ID saved');
    } catch (e: any) {
      toast.error(e.response?.data?.detail ?? 'Failed to save UPI ID');
    } finally {
      setSaving(false);
    }
  };

  const handleUploadPhoto = async (file: File) => {
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) {
      toast.error('Photo must be under 2 MB');
      return;
    }
    setUploading(true);
    try {
      const { upload_url, key } = await userApi.getAvatarUploadUrl();
      const presigned = await fetch(upload_url, {
        method: 'PUT',
        headers: { 'Content-Type': 'image/jpeg' },
        body: file,
      });
      if (!presigned.ok) throw new Error('Upload failed');
      await userApi.updateMe({ avatar_key: key });
      await refreshUser();
      if (activeRoomId) await fetchMembers(activeRoomId);
      toast.success('Profile photo updated');
    } catch (e: any) {
      toast.error(e.response?.data?.detail ?? e.message ?? 'Failed to upload photo');
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = '';
    }
  };

  const handleDeleteAccount = async () => {
    const ok = await confirm({
      title: 'Delete your account?',
      message: 'This permanently deletes your profile and removes you from all rooms. Expenses you created remain.',
      confirmLabel: 'Delete account',
      danger: true,
    });
    if (!ok) return;
    setSaving(true);
    try {
      await userApi.deleteMe();
      toast.success('Account deleted');
      await signOut();
      window.location.href = '/login';
    } catch (e: any) {
      toast.error(e.response?.data?.detail ?? 'Failed to delete account');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fm-page">
      <header className="fm-topbar">
        <div style={s.topLeft}>
          <span style={s.breadcrumb}>Account</span>
          <span style={s.sep}>/</span>
          <span style={s.pageTitle}>Profile & settings</span>
        </div>
        {saved && <span style={s.savedTag}>Saved!</span>}
      </header>

      <div className="fm-profile-grid">

        {/* Settings nav */}
        <div style={s.settingsNav}>
          {NAV.map(n => (
            <div key={n.id} onClick={() => setActive(n.id)}
              style={{ ...s.navItem, ...(active === n.id ? s.navItemActive : {}) }}>
              {n.label}
            </div>
          ))}
          <div style={s.navDivider} />
          <div style={{ ...s.navItem, color: 'var(--text-danger)', cursor: 'pointer' }}
            onClick={signOut}>
            Sign out
          </div>
        </div>

        {/* Panels */}
        <div style={s.panels}>

          {/* Profile */}
          <div className="fm-card">
            <div style={s.cardTitle}>Your profile</div>
            <div style={s.avatarSection}>
              {user && <Avatar name={user.name} userId={user.id} avatarUrl={user.avatar_url} size={60} />}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={s.avName}>{user?.name}</div>
                <div style={s.avEmail}>{user?.email}</div>
                <div style={s.avMeta}>Member since {user ? new Date(user.created_at).toLocaleDateString('en-IN', { month: 'short', year: 'numeric' }) : '—'}</div>
              </div>
              <input
                ref={fileRef}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                style={{ display: 'none' }}
                onChange={e => { const f = e.target.files?.[0]; if (f) handleUploadPhoto(f); }}
              />
              <button style={s.uploadBtn} onClick={() => fileRef.current?.click()} disabled={uploading}>
                {uploading ? 'Uploading…' : 'Change photo'}
              </button>
            </div>
            <div style={s.twoFields}>
              <div style={s.field}><label style={s.label}>Full name</label>
                <input style={s.input} value={name} onChange={e => setName(e.target.value)} /></div>
              <div style={s.field}><label style={s.label}>Email</label>
                <input style={{ ...s.input, background: 'var(--bg-secondary)', color: 'var(--text-tertiary)' }} value={user?.email ?? ''} readOnly />
                <span style={s.hint}>Managed via Google OAuth · Supabase</span></div>
            </div>
            <div style={{ ...s.field, marginTop: '0.75rem' }}>
              <label style={s.label}>Phone</label>
              <input style={s.input} value={phone} placeholder="+91 98765 43210" onChange={e => setPhone(e.target.value)} />
            </div>
            <div style={s.btnRow}>
              <Button variant="primary" loading={saving} onClick={saveProfile}>Save profile</Button>
              <Button variant="ghost" onClick={() => { setName(user?.name ?? ''); setPhone(user?.phone ?? ''); setUpi(user?.upi_id ?? ''); }}>Cancel</Button>
            </div>
          </div>

          {/* Payment info */}
          <div className="fm-card">
            <div style={s.cardTitle}>Payment info</div>
            <p style={s.cardDesc}>Your UPI ID is shown to flatmates when they need to pay you.</p>
            <div style={s.field}>
              <label style={s.label}>UPI ID</label>
              <input style={s.input} value={upi} placeholder="yourname@okaxis" onChange={e => setUpi(e.target.value)} />
              <span style={s.hint}>Shown to flatmates on the Payments screen</span>
            </div>
            <div style={{ marginTop: '0.85rem' }}>
              <Button variant="primary" loading={saving} onClick={saveUpi}>Save UPI ID</Button>
            </div>
          </div>

          {/* Notifications */}
          <div className="fm-card">
            <div style={s.cardTitle}>Notifications</div>
            {[
              { key: 'newExpense',       label: 'New expense added',   desc: 'When a flatmate adds an expense that includes you' },
              { key: 'paymentReceived',  label: 'Payment received',    desc: 'When someone marks a payment to you as sent' },
              { key: 'smartReminders',  label: 'Smart reminders',     desc: 'AI-powered nudges for recurring expenses' },
              { key: 'weekly',          label: 'Weekly summary',      desc: 'A weekly digest of your balances' },
            ].map((n, i, arr) => (
              <div key={n.key} style={{ ...s.toggleRow, ...(i === arr.length - 1 ? { borderBottom: 'none' } : {}) }}>
                <div style={{ flex: 1, marginRight: '1rem' }}>
                  <div style={s.toggleLabel}>{n.label}</div>
                  <div style={s.toggleDesc}>{n.desc}</div>
                </div>
                <label style={s.toggle}>
                  <input type="checkbox" checked={notifs[n.key as keyof typeof notifs]}
                    onChange={() => setNotifs(p => ({ ...p, [n.key]: !p[n.key as keyof typeof notifs] }))}
                    style={{ position: 'absolute', opacity: 0, width: 0, height: 0 }} />
                  <span style={{
                    position: 'absolute', inset: 0, borderRadius: 9999,
                    background: notifs[n.key as keyof typeof notifs] ? '#ccff00' : 'var(--bg-tertiary)',
                    border: `0.5px solid ${notifs[n.key as keyof typeof notifs] ? '#ccff00' : 'var(--border-mid)'}`,
                    transition: 'background 0.2s',
                  }}>
                    <span style={{
                      position: 'absolute', width: 14, height: 14, borderRadius: '50%',
                      left: notifs[n.key as keyof typeof notifs] ? 19 : 3, top: 2.5,
                      background: notifs[n.key as keyof typeof notifs] ? '#000' : 'var(--bg-primary)',
                      transition: 'left 0.2s', boxShadow: '0 1px 3px rgba(0,0,0,0.25)',
                    }} />
                  </span>
                </label>
              </div>
            ))}
          </div>

          {/* Danger zone */}
          <div style={s.dangerZone}>
            <div style={s.dzTitle}>Delete account</div>
            <div style={s.dzDesc}>Permanently deletes your profile and removes you from all rooms. Expenses you created remain.</div>
            <Button variant="danger" onClick={handleDeleteAccount}>Delete my account</Button>
          </div>

        </div>
      </div>
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  topLeft:     { display: 'flex', alignItems: 'center', gap: 10 },
  breadcrumb:  { fontSize: 13, color: 'var(--text-tertiary)' },
  sep:         { color: 'var(--border-mid)' },
  pageTitle:   { fontSize: 15, fontWeight: 500 },
  savedTag:    { fontSize: 12, background: 'var(--bg-success)', color: 'var(--text-success)', padding: '4px 12px', borderRadius: 9999, fontWeight: 500 },
  settingsNav: { background: 'var(--bg-primary)', border: '0.5px solid var(--border-light)', borderRadius: 'var(--r-lg)', padding: '0.4rem', display: 'flex', flexDirection: 'column', gap: 2, position: 'sticky', top: '1.25rem' },
  navItem:     { padding: '0.5rem 0.75rem', borderRadius: 'var(--r-md)', fontSize: 13, color: 'var(--text-secondary)', cursor: 'pointer' },
  navItemActive:{ background: 'var(--bg-secondary)', color: 'var(--text-primary)', fontWeight: 500 },
  navDivider:  { height: '0.5px', background: 'var(--border-light)', margin: '4px 0' },
  panels:      { display: 'flex', flexDirection: 'column', gap: '1.1rem' },
  cardTitle:   { fontSize: 13.5, fontWeight: 600, marginBottom: '0.85rem' },
  cardDesc:    { fontSize: 12, color: 'var(--text-tertiary)', lineHeight: 1.5, marginBottom: '0.85rem' },
  avatarSection:{ display: 'flex', alignItems: 'center', gap: '1.1rem', background: 'var(--bg-secondary)', borderRadius: 'var(--r-md)', padding: '1rem', marginBottom: '1rem' },
  avName:      { fontSize: 16, fontWeight: 500 },
  avEmail:     { fontSize: 12, color: 'var(--text-tertiary)', marginTop: 2, wordBreak: 'break-all' },
  avMeta:      { fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 },
  uploadBtn:   { background: 'transparent', border: '0.5px solid var(--border-mid)', borderRadius: 'var(--r-md)', height: 30, padding: '0 12px', fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)', color: 'var(--text-secondary)' },
  twoFields:   { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 },
  field:       { display: 'flex', flexDirection: 'column', gap: 5, marginBottom: '0.75rem' },
  label:       { fontSize: 12, color: 'var(--text-secondary)', fontWeight: 500 },
  input:       { height: 34, padding: '0 10px', borderRadius: 'var(--r-md)', border: '0.5px solid var(--border-mid)', background: 'var(--bg-primary)', color: 'var(--text-primary)', fontSize: 13, fontFamily: 'var(--font-sans)', outline: 'none', width: '100%' },
  hint:        { fontSize: 11, color: 'var(--text-tertiary)' },
  btnRow:      { display: 'flex', gap: 8, marginTop: '0.85rem', flexWrap: 'wrap' },
  toggleRow:   { display: 'flex', alignItems: 'center', padding: '0.65rem 0', borderBottom: '0.5px solid var(--border-light)' },
  toggleLabel: { fontSize: 13, fontWeight: 500 },
  toggleDesc:  { fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2, lineHeight: 1.4 },
  toggle:      { position: 'relative', width: 36, height: 20, flexShrink: 0, cursor: 'pointer', display: 'block' },
  dangerZone:  { border: '0.5px solid var(--danger-border)', borderRadius: 'var(--r-lg)', padding: '1.25rem', background: 'var(--bg-danger)' },
  dzTitle:     { fontSize: 14, fontWeight: 500, color: 'var(--text-danger)', marginBottom: 5 },
  dzDesc:      { fontSize: 12, color: 'var(--text-danger)', opacity: 0.75, lineHeight: 1.5, marginBottom: '0.85rem' },
};

import React from 'react';