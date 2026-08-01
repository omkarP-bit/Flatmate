import { useEffect } from 'react';
import { useExpenseStore } from '../store/expenseStore';
import { useRoomStore } from '../store/roomStore';
import { useToast } from '../components/common/Toast';
import { useConfirm } from '../components/common/Confirm';
import { ExpenseCreate } from '../types/expense.types';

export function useExpenses() {
  const { activeRoomId } = useRoomStore();
  const {
    expenses, balance, suggestions, loading, error,
    fetchExpenses, createExpense, deleteExpense,
    settleSplit, fetchMyBalance, fetchSuggestions,
  } = useExpenseStore();
  const toast = useToast();
  const { confirm } = useConfirm();

  useEffect(() => {
    if (!activeRoomId) return;
    fetchExpenses(activeRoomId);
    fetchMyBalance(activeRoomId);
    fetchSuggestions(activeRoomId);
  }, [activeRoomId]);

  const handleCreate = async (data: ExpenseCreate) => {
    const exp = await createExpense(data);
    if (activeRoomId) await fetchMyBalance(activeRoomId);
    toast.success('Expense added');
    return exp;
  };

  const handleDelete = async (expenseId: number) => {
    if (!activeRoomId) return;
    const ok = await confirm({
      title: 'Delete this expense?',
      message: 'This removes the expense and all its splits. Balances will be recalculated.',
      confirmLabel: 'Delete',
      danger: true,
    });
    if (!ok) return;
    try {
      await deleteExpense(expenseId, activeRoomId);
      toast.success('Expense deleted');
    } catch (e: any) {
      toast.error(e.response?.data?.detail ?? e.message ?? 'Failed to delete expense');
    }
  };

  const handleSettle = async (expenseId: number) => {
    try {
      await settleSplit(expenseId);
      if (activeRoomId) await fetchMyBalance(activeRoomId);
      toast.success('Marked as settled');
    } catch (e: any) {
      toast.error(e.response?.data?.detail ?? e.message ?? 'Failed to settle');
    }
  };

  // Group expenses by month label
  const grouped = expenses.reduce<Record<string, typeof expenses>>((acc, e) => {
    const key = new Date(e.created_at).toLocaleDateString('en-IN', { month: 'long', year: 'numeric' });
    if (!acc[key]) acc[key] = [];
    acc[key].push(e);
    return acc;
  }, {});

  return {
    expenses, grouped, balance, suggestions,
    loading, error,
    handleCreate, handleDelete, handleSettle,
  };
}