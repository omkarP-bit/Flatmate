import { expenseClient } from './client';
import {
  Expense, ExpenseCreate, UserBalanceOut,
  BalanceEntry, CategorySuggestion, RecurringSuggestion,
} from '../types/expense.types';

const toNum = (v: any): number => {
  const n = Number(v);
  return Number.isFinite(n) ? n : 0;
};

function normalizeExpense(e: any): Expense {
  return {
    ...e,
    amount: toNum(e.amount),
    splits: (e.splits ?? []).map((s: any) => ({
      ...s,
      amount: toNum(s.amount),
      expense_id: toNum(s.expense_id),
    })),
  };
}

function normalizeBalance(b: any): UserBalanceOut {
  if (!b) return b;
  return {
    ...b,
    owed_to_me: toNum(b.owed_to_me),
    i_owe: toNum(b.i_owe),
    net: toNum(b.net),
    details: (b.details ?? []).map((d: any) => ({ ...d, amount: toNum(d.amount) })),
  };
}

export const expenseApi = {
  create: (data: ExpenseCreate) =>
    expenseClient.post<Expense>('/expenses', data).then(r => normalizeExpense(r.data)),

  getByRoom: (roomId: number) =>
    expenseClient.get<Expense[]>('/expenses/room/' + roomId).then(r => (r.data ?? []).map(normalizeExpense)),

  getById: (expenseId: number) =>
    expenseClient.get<Expense>('/expenses/' + expenseId).then(r => normalizeExpense(r.data)),

  deleteById: (expenseId: number) =>
    expenseClient.delete<{ message: string }>('/expenses/' + expenseId).then(r => r.data),

  settleSplit: (expenseId: number) =>
    expenseClient.patch<{ message: string }>('/expenses/' + expenseId + '/settle').then(r => r.data),

  suggestCategory: (title: string) =>
    expenseClient.get<CategorySuggestion>('/expenses/suggest/category', { params: { title } }).then(r => r.data),

  getRecurringSuggestions: (roomId: number) =>
    expenseClient.get<RecurringSuggestion[]>(`/expenses/suggest/recurring/${roomId}`).then(r =>
      (r.data ?? []).map(s => ({ ...s, avg_amount: toNum(s.avg_amount), days_since: toNum(s.days_since) }))
    ),

  getRoomBalances: (roomId: number) =>
    expenseClient.get<BalanceEntry[]>('/expenses/balance/room/' + roomId).then(r =>
      (r.data ?? []).map(d => ({ ...d, amount: toNum(d.amount) }))
    ),

  getMyBalance: (roomId: number) =>
    expenseClient.get<UserBalanceOut>('/expenses/balance/me/room/' + roomId).then(r => normalizeBalance(r.data)),
};