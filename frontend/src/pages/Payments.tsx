import { useState, useEffect } from 'react';
import { paymentApi } from '../api/paymentApi';
import { Payment, PaymentSummary } from '../types/payments.types';
import { useAuthStore } from '../store/authStore';
import PaymentsRow from '../components/payments/PaymentsRow';
import RecordPaymentForm from '../components/payments/RecordPaymentForm';
import Modal from '../components/common/Modal';
import Button from '../components/common/Button';
import StatCard from '../components/common/StatCard';
import RoomSwitcher from '../components/common/RoomSwitcher';
import Loader from '../components/common/Loader';
import { useToast } from '../components/common/Toast';
import { formatAmount } from '../utils/formateCurrency';

type Filter = 'all' | 'pending' | 'settled';

export default function Payments() {
  const { user } = useAuthStore();
  const toast = useToast();
  const [payments,  setPayments]  = useState<Payment[]>([]);
  const [summary,   setSummary]   = useState<PaymentSummary | null>(null);
  const [filter,    setFilter]    = useState<Filter>('all');
  const [loading,   setLoading]   = useState(true);
  const [showForm,  setShowForm]  = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [p, s] = await Promise.all([paymentApi.getMyPayments(), paymentApi.getMySummary()]);
      setPayments(p);
      setSummary(s);
    } catch (e: any) {
      toast.error(e.response?.data?.detail ?? 'Failed to load payments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleConfirm = async (paymentId: number) => {
    try {
      await paymentApi.settle(paymentId, {});
      toast.success('Payment confirmed');
      load();
    } catch (e: any) {
      toast.error(e.response?.data?.detail ?? 'Failed to confirm payment');
    }
  };

  const shown = payments.filter(p =>
    filter === 'all' ? true : p.status === filter
  );

  return (
    <div className="fm-page">
      <header className="fm-topbar">
        <div style={s.topLeft}>
          <RoomSwitcher />
          <span style={s.sep}>/</span>
          <span style={s.pageTitle}>Payments</span>
        </div>
        <Button variant="primary" size="sm" onClick={() => setShowForm(true)}
          icon={<svg width="11" height="11" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2"><path d="M6 1v10M1 6h10"/></svg>}>
          Record payment
        </Button>
      </header>

      <div className="fm-content">
        {loading && <Loader />}

        {/* Stats */}
        <div className="fm-grid-4">
          <StatCard label="Total paid out"   value={formatAmount(summary?.total_paid      ?? 0)} sub="Settled" />
          <StatCard label="Total received"   value={formatAmount(summary?.total_received  ?? 0)} sub="Confirmed" valueColor="var(--text-success)" />
          <StatCard label="Pending out"      value={formatAmount(summary?.pending_out     ?? 0)} sub="Awaiting confirmation" valueColor="var(--text-danger)" />
          <StatCard label="Pending in"       value={formatAmount(summary?.pending_in      ?? 0)} sub="From flatmates" valueColor="var(--text-warning)" />
        </div>

        <div className="fm-two-col">

          {/* History */}
          <div className="fm-card">
            <div style={s.cardHeader}>
              <span style={s.cardTitle}>Payment history</span>
              <div style={s.filterRow}>
                {(['all','pending','settled'] as Filter[]).map(f => (
                  <button key={f} onClick={() => setFilter(f)}
                    style={{ ...s.chip, ...(filter === f ? s.chipActive : {}) }}>
                    {f.charAt(0).toUpperCase() + f.slice(1)}
                  </button>
                ))}
              </div>
            </div>
            {shown.length === 0
              ? <div style={s.empty}>No payments found.</div>
              : shown.map(p => (
                  <PaymentsRow key={p.id} payment={p} onConfirm={handleConfirm} />
                ))
            }
          </div>

          {/* Quick record form */}
          <div className="fm-card">
            <div style={s.cardHeader}><span style={s.cardTitle}>Send a payment</span></div>
            <RecordPaymentForm onSuccess={load} />
          </div>

        </div>
      </div>

      {showForm && (
        <Modal title="Record payment" onClose={() => setShowForm(false)}>
          <RecordPaymentForm onClose={() => setShowForm(false)} onSuccess={() => { load(); setShowForm(false); }} />
        </Modal>
      )}
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  topLeft:    { display: 'flex', alignItems: 'center', gap: 10 },
  breadcrumb: { fontSize: 13, color: 'var(--text-tertiary)' },
  sep:        { color: 'var(--border-mid)' },
  pageTitle:  { fontSize: 15, fontWeight: 500 },
  cardHeader: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.85rem', gap: 8, flexWrap: 'wrap' },
  cardTitle:  { fontSize: 13.5, fontWeight: 600 },
  filterRow:  { display: 'flex', gap: 5, flexWrap: 'wrap' },
  chip:       { padding: '3px 12px', borderRadius: 9999, border: '0.5px solid var(--border-light)', background: 'transparent', fontSize: 12, cursor: 'pointer', color: 'var(--text-secondary)', fontFamily: 'var(--font-sans)' },
  chipActive: { background: '#ccff00', color: '#000', borderColor: '#ccff00', fontWeight: 500 },
  empty:      { fontSize: 13, color: 'var(--text-tertiary)', textAlign: 'center', padding: '2rem 0' },
};

import React from 'react';