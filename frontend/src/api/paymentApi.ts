import { paymentClient } from './client';
import { Payment, PaymentCreate, PaymentSettle, PaymentSummary } from '../types/payments.types';

const toNum = (v: any): number => {
  const n = Number(v);
  return Number.isFinite(n) ? n : 0;
};

function normalizePayment(p: any): Payment {
  return { ...p, amount: toNum(p.amount), room_id: toNum(p.room_id) };
}

function normalizeSummary(s: any): PaymentSummary {
  return {
    total_paid: toNum(s?.total_paid),
    total_received: toNum(s?.total_received),
    pending_out: toNum(s?.pending_out),
    pending_in: toNum(s?.pending_in),
    transaction_count: toNum(s?.transaction_count),
  };
}

export const paymentApi = {
  create: (data: PaymentCreate) =>
    paymentClient.post<Payment>('/payments', data).then(r => normalizePayment(r.data)),

  getMyPayments: () =>
    paymentClient.get<Payment[]>('/payments/me').then(r => (r.data ?? []).map(normalizePayment)),

  getMySummary: () =>
    paymentClient.get<PaymentSummary>('/payments/me/summary').then(r => normalizeSummary(r.data)),

  getRoomPayments: (roomId: number, status?: 'pending' | 'settled') =>
    paymentClient.get<Payment[]>(`/payments/room/${roomId}`, { params: status ? { status } : {} }).then(r => (r.data ?? []).map(normalizePayment)),

  settle: (paymentId: number, data: PaymentSettle) =>
    paymentClient.patch<Payment>(`/payments/${paymentId}/settle`, data).then(r => normalizePayment(r.data)),

  getById: (paymentId: number) =>
    paymentClient.get<Payment>(`/payments/${paymentId}`).then(r => normalizePayment(r.data)),
};