"""Phase 3 Tests — Expense Service: models, schemas, split calculator, smart suggest, balance engine."""

import os
import subprocess
import sys
from decimal import Decimal

SHARED = os.path.join(os.path.dirname(__file__), '..', 'shared')
SERVICES = os.path.join(os.path.dirname(__file__), '..', 'services')

ENV = {
    **os.environ,
    'SUPABASE_URL': 'https://test.supabase.co',
    'SUPABASE_SERVICE_KEY': 'test-key',
    'SUPABASE_JWT_SECRET': 'test-secret',
    'ENVIRONMENT': 'development',
    'SERVICE_NAME': 'expense-service',
}


def _read_source(filename: str) -> str:
    path = os.path.join(SERVICES, 'expense-service', 'src', filename)
    with open(path) as f:
        return f.read()


def _run_isolated(test_code: str):
    src_dir = os.path.join(SERVICES, 'expense-service', 'src')
    code = (
        f"import sys; sys.path.insert(0, {SHARED!r}); sys.path.insert(0, {src_dir!r})\n"
        + test_code
    )
    result = subprocess.run(
        [sys.executable, '-c', code],
        capture_output=True, text=True, env=ENV, timeout=10,
    )
    return result


# ── Model Source Code Analysis ──────────────────────────────────


class TestExpenseModels:
    """Verify expense-service models via source code analysis."""

    def test_expense_tablename(self):
        assert '__tablename__ = "expenses"' in _read_source('models.py')

    def test_expense_split_tablename(self):
        assert '__tablename__ = "expense_splits"' in _read_source('models.py')

    def test_expense_has_required_columns(self):
        source = _read_source('models.py')
        for col in ['id', 'room_id', 'title', 'amount', 'category', 'paid_by', 'split_type', 'notes', 'created_at']:
            assert col in source, f"Missing column: {col}"

    def test_expense_split_has_required_columns(self):
        source = _read_source('models.py')
        for col in ['id', 'expense_id', 'user_id', 'amount', 'is_settled', 'settled_at']:
            assert col in source, f"Missing split column: {col}"

    def test_paid_by_references_profiles(self):
        assert 'ForeignKey("profiles.id")' in _read_source('models.py')

    def test_room_id_references_rooms(self):
        assert 'ForeignKey("rooms.id"' in _read_source('models.py')

    def test_expense_id_references_expenses(self):
        assert 'ForeignKey("expenses.id"' in _read_source('models.py')

    def test_has_split_type_enum(self):
        source = _read_source('models.py')
        assert '"equal"' in source
        assert '"custom"' in source
        assert '"percentage"' in source

    def test_has_expense_category_enum(self):
        source = _read_source('models.py')
        assert '"rent"' in source
        assert '"electricity"' in source
        assert '"groceries"' in source
        assert '"utilities"' in source
        assert '"other"' in source

    def test_has_relationship(self):
        assert 'relationship("ExpenseSplit"' in _read_source('models.py')

    def test_imports_from_database(self):
        assert 'from database import Base' in _read_source('models.py')


# ── Schema Tests ────────────────────────────────────────────────


class TestExpenseSchemas:
    """Test expense-service schemas via isolated import."""

    def test_expense_create_minimal(self):
        result = _run_isolated(
            "from decimal import Decimal\n"
            "from schemas import ExpenseCreate\n"
            "e = ExpenseCreate(room_id=1, title='Rent', amount=Decimal('5000.00'),\n"
            "    members=['u1','u2'])\n"
            "assert e.split_type == 'equal'\n"
            "assert e.category == 'other'\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_expense_create_with_category(self):
        result = _run_isolated(
            "from decimal import Decimal\n"
            "from schemas import ExpenseCreate\n"
            "e = ExpenseCreate(room_id=1, title='Power bill', amount=Decimal('1200.00'),\n"
            "    category='electricity', split_type='equal', members=['u1','u2'])\n"
            "assert e.category == 'electricity'\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_expense_create_invalid_amount(self):
        result = _run_isolated(
            "from decimal import Decimal\n"
            "from pydantic import ValidationError\n"
            "from schemas import ExpenseCreate\n"
            "try:\n"
            "    ExpenseCreate(room_id=1, title='X', amount=Decimal('-10'),\n"
            "        members=['u1'])\n"
            "    assert False, 'Should have raised'\n"
            "except ValidationError:\n"
            "    print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_expense_create_zero_amount(self):
        result = _run_isolated(
            "from decimal import Decimal\n"
            "from pydantic import ValidationError\n"
            "from schemas import ExpenseCreate\n"
            "try:\n"
            "    ExpenseCreate(room_id=1, title='X', amount=Decimal('0'),\n"
            "        members=['u1'])\n"
            "    assert False, 'Should have raised'\n"
            "except ValidationError:\n"
            "    print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_expense_out_fields(self):
        result = _run_isolated(
            "from schemas import ExpenseOut\n"
            "f = ExpenseOut.model_fields\n"
            "assert all(k in f for k in ['id','room_id','title','amount','category','paid_by','split_type','splits'])\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_split_out_fields(self):
        result = _run_isolated(
            "from schemas import SplitOut\n"
            "f = SplitOut.model_fields\n"
            "assert all(k in f for k in ['expense_id','user_id','amount','is_settled','settled_at'])\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_balance_entry_fields(self):
        result = _run_isolated(
            "from schemas import BalanceEntry\n"
            "f = BalanceEntry.model_fields\n"
            "assert all(k in f for k in ['from_user','to_user','amount'])\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_user_balance_out_fields(self):
        result = _run_isolated(
            "from schemas import UserBalanceOut\n"
            "f = UserBalanceOut.model_fields\n"
            "assert all(k in f for k in ['user_id','room_id','owed_to_me','i_owe','net','details'])\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_category_suggestion_fields(self):
        result = _run_isolated(
            "from schemas import CategorySuggestion\n"
            "f = CategorySuggestion.model_fields\n"
            "assert all(k in f for k in ['category','confidence','source'])\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_recurring_suggestion_fields(self):
        result = _run_isolated(
            "from schemas import RecurringSuggestion\n"
            "f = RecurringSuggestion.model_fields\n"
            "assert all(k in f for k in ['category','title','avg_amount','last_added','days_since','message'])\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_custom_split_entry_fields(self):
        result = _run_isolated(
            "from schemas import CustomSplitEntry\n"
            "f = CustomSplitEntry.model_fields\n"
            "assert all(k in f for k in ['user_id','amount'])\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr


# ── Split Calculator Tests ──────────────────────────────────────


class TestSplitCalculator:
    """Test split_calculator.py logic via isolated import."""

    def test_equal_split_basic(self):
        result = _run_isolated(
            "from decimal import Decimal\n"
            "from schemas import ExpenseCreate\n"
            "from split_calculator import calculate_splits\n"
            "data = ExpenseCreate(room_id=1, title='E', amount=Decimal('2400.00'),\n"
            "    split_type='equal', members=['u1','u2','u3','u4'])\n"
            "splits = calculate_splits(data)\n"
            "assert len(splits) == 4\n"
            "assert all(s['amount'] == 600.00 for s in splits)\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_equal_split_two_members(self):
        result = _run_isolated(
            "from decimal import Decimal\n"
            "from schemas import ExpenseCreate\n"
            "from split_calculator import calculate_splits\n"
            "data = ExpenseCreate(room_id=1, title='E', amount=Decimal('1000.00'),\n"
            "    split_type='equal', members=['a','b'])\n"
            "splits = calculate_splits(data)\n"
            "assert len(splits) == 2\n"
            "assert splits[0]['amount'] == 500.00\n"
            "assert splits[1]['amount'] == 500.00\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_equal_split_rounding(self):
        result = _run_isolated(
            "from decimal import Decimal\n"
            "from schemas import ExpenseCreate\n"
            "from split_calculator import calculate_splits\n"
            "data = ExpenseCreate(room_id=1, title='G', amount=Decimal('100.00'),\n"
            "    split_type='equal', members=['a','b','c'])\n"
            "splits = calculate_splits(data)\n"
            "total = sum(Decimal(str(s['amount'])) for s in splits)\n"
            "assert total == Decimal('100.00'), f'Total was {total}'\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_equal_split_last_person_fixes_remainder(self):
        result = _run_isolated(
            "from decimal import Decimal\n"
            "from schemas import ExpenseCreate\n"
            "from split_calculator import calculate_splits\n"
            "data = ExpenseCreate(room_id=1, title='B', amount=Decimal('100.00'),\n"
            "    split_type='equal', members=['a','b','c'])\n"
            "splits = calculate_splits(data)\n"
            "amounts = [s['amount'] for s in splits]\n"
            "assert amounts[0] == 33.33\n"
            "assert amounts[1] == 33.33\n"
            "assert amounts[2] == 33.34\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_equal_split_five_members(self):
        result = _run_isolated(
            "from decimal import Decimal\n"
            "from schemas import ExpenseCreate\n"
            "from split_calculator import calculate_splits\n"
            "data = ExpenseCreate(room_id=1, title='E', amount=Decimal('500.00'),\n"
            "    split_type='equal', members=['a','b','c','d','e'])\n"
            "splits = calculate_splits(data)\n"
            "total = sum(Decimal(str(s['amount'])) for s in splits)\n"
            "assert total == Decimal('500.00'), f'Total was {total}'\n"
            "assert len(splits) == 5\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_custom_split(self):
        result = _run_isolated(
            "from decimal import Decimal\n"
            "from schemas import ExpenseCreate\n"
            "from split_calculator import calculate_splits\n"
            "data = ExpenseCreate(room_id=1, title='C', amount=Decimal('100.00'),\n"
            "    split_type='custom', members=['a','b'],\n"
            "    splits=[{'user_id':'a','amount':Decimal('70')},\n"
            "    {'user_id':'b','amount':'30'}])\n"
            "splits = calculate_splits(data)\n"
            "assert len(splits) == 2\n"
            "assert splits[0]['amount'] == 70.00\n"
            "assert splits[1]['amount'] == 30.00\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_custom_split_three_members(self):
        result = _run_isolated(
            "from decimal import Decimal\n"
            "from schemas import ExpenseCreate\n"
            "from split_calculator import calculate_splits\n"
            "data = ExpenseCreate(room_id=1, title='C', amount=Decimal('300.00'),\n"
            "    split_type='custom', members=['a','b','c'],\n"
            "    splits=[{'user_id':'a','amount':Decimal('150')},\n"
            "    {'user_id':'b','amount':'100'},\n"
            "    {'user_id':'c','amount':'50'}])\n"
            "splits = calculate_splits(data)\n"
            "total = sum(Decimal(str(s['amount'])) for s in splits)\n"
            "assert total == Decimal('300.00')\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_custom_split_mismatch_raises(self):
        result = _run_isolated(
            "from decimal import Decimal\n"
            "from schemas import ExpenseCreate\n"
            "from split_calculator import calculate_splits\n"
            "from fastapi import HTTPException\n"
            "data = ExpenseCreate(room_id=1, title='C', amount=Decimal('100.00'),\n"
            "    split_type='custom', members=['a','b'],\n"
            "    splits=[{'user_id':'a','amount':Decimal('100')}])\n"
            "try:\n"
            "    calculate_splits(data)\n"
            "    assert False, 'Should have raised'\n"
            "except HTTPException as e:\n"
            "    assert e.status_code == 400\n"
            "    print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_custom_split_sum_mismatch_raises(self):
        result = _run_isolated(
            "from decimal import Decimal\n"
            "from schemas import ExpenseCreate\n"
            "from split_calculator import calculate_splits\n"
            "from fastapi import HTTPException\n"
            "data = ExpenseCreate(room_id=1, title='C', amount=Decimal('100.00'),\n"
            "    split_type='custom', members=['a','b'],\n"
            "    splits=[{'user_id':'a','amount':Decimal('60')},\n"
            "    {'user_id':'b','amount':'30'}])\n"
            "try:\n"
            "    calculate_splits(data)\n"
            "    assert False, 'Should have raised'\n"
            "except HTTPException as e:\n"
            "    assert e.status_code == 400\n"
            "    print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_percentage_split(self):
        result = _run_isolated(
            "from decimal import Decimal\n"
            "from schemas import ExpenseCreate\n"
            "from split_calculator import calculate_splits\n"
            "data = ExpenseCreate(room_id=1, title='P', amount=Decimal('1000.00'),\n"
            "    split_type='percentage', members=['a','b'],\n"
            "    splits=[{'user_id':'a','amount':Decimal('60')},\n"
            "    {'user_id':'b','amount':'40'}])\n"
            "splits = calculate_splits(data)\n"
            "assert len(splits) == 2\n"
            "assert splits[0]['amount'] == 600.00\n"
            "assert splits[1]['amount'] == 400.00\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_percentage_split_three_members(self):
        result = _run_isolated(
            "from decimal import Decimal\n"
            "from schemas import ExpenseCreate\n"
            "from split_calculator import calculate_splits\n"
            "data = ExpenseCreate(room_id=1, title='P', amount=Decimal('900.00'),\n"
            "    split_type='percentage', members=['a','b','c'],\n"
            "    splits=[{'user_id':'a','amount':Decimal('50')},\n"
            "    {'user_id':'b','amount':'30'},\n"
            "    {'user_id':'c','amount':'20'}])\n"
            "splits = calculate_splits(data)\n"
            "total = sum(Decimal(str(s['amount'])) for s in splits)\n"
            "assert total == Decimal('900.00'), f'Total was {total}'\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_percentage_not_100_raises(self):
        result = _run_isolated(
            "from decimal import Decimal\n"
            "from schemas import ExpenseCreate\n"
            "from split_calculator import calculate_splits\n"
            "from fastapi import HTTPException\n"
            "data = ExpenseCreate(room_id=1, title='P', amount=Decimal('100.00'),\n"
            "    split_type='percentage', members=['a','b'],\n"
            "    splits=[{'user_id':'a','amount':Decimal('60')},\n"
            "    {'user_id':'b','amount':'50'}])\n"
            "try:\n"
            "    calculate_splits(data)\n"
            "    assert False, 'Should have raised'\n"
            "except HTTPException as e:\n"
            "    assert e.status_code == 400\n"
            "    print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_empty_members_raises(self):
        result = _run_isolated(
            "from decimal import Decimal\n"
            "from schemas import ExpenseCreate\n"
            "from split_calculator import calculate_splits\n"
            "from fastapi import HTTPException\n"
            "data = ExpenseCreate(room_id=1, title='E', amount=Decimal('100.00'),\n"
            "    split_type='equal', members=[])\n"
            "try:\n"
            "    calculate_splits(data)\n"
            "    assert False, 'Should have raised'\n"
            "except HTTPException as e:\n"
            "    assert e.status_code == 400\n"
            "    print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_unknown_split_type_raises(self):
        result = _run_isolated(
            "from decimal import Decimal\n"
            "from schemas import ExpenseCreate\n"
            "from split_calculator import calculate_splits\n"
            "from fastapi import HTTPException\n"
            "data = ExpenseCreate(room_id=1, title='E', amount=Decimal('100.00'),\n"
            "    split_type='equal', members=['a'])\n"
            "data.split_type = 'bogus'\n"
            "try:\n"
            "    calculate_splits(data)\n"
            "    assert False, 'Should have raised'\n"
            "except HTTPException as e:\n"
            "    assert e.status_code == 400\n"
            "    print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_split_result_user_ids_match(self):
        result = _run_isolated(
            "from decimal import Decimal\n"
            "from schemas import ExpenseCreate\n"
            "from split_calculator import calculate_splits\n"
            "members = ['u1', 'u2', 'u3']\n"
            "data = ExpenseCreate(room_id=1, title='E', amount=Decimal('300.00'),\n"
            "    split_type='equal', members=members)\n"
            "splits = calculate_splits(data)\n"
            "split_ids = [s['user_id'] for s in splits]\n"
            "assert split_ids == members\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr


# ── Smart Suggest Tests ─────────────────────────────────────────


class TestSmartSuggest:
    """Test smart_suggest.py logic via isolated import."""

    def _run_predict(self, title):
        result = _run_isolated(
            f"from smart_suggest import predict_category\n"
            f"r = predict_category({title!r})\n"
            f"print(r)"
        )
        assert result.returncode == 0, result.stderr
        return result.stdout.strip()

    def test_predict_rent(self):
        assert self._run_predict("rent for april") == "rent"

    def test_predict_rent_landlord(self):
        assert self._run_predict("pay landlord") == "rent"

    def test_predict_electricity(self):
        assert self._run_predict("MSEDCL power bill") == "electricity"

    def test_predict_electricity_bescom(self):
        assert self._run_predict("bescom bill") == "electricity"

    def test_predict_groceries(self):
        assert self._run_predict("bigbasket order") == "groceries"

    def test_predict_groceries_zepto(self):
        assert self._run_predict("zepto delivery") == "groceries"

    def test_predict_groceries_dmart(self):
        assert self._run_predict("dmart shopping") == "groceries"

    def test_predict_utilities(self):
        assert self._run_predict("jio wifi bill") == "utilities"

    def test_predict_utilities_water(self):
        assert self._run_predict("water bill") == "utilities"

    def test_predict_utilities_gas(self):
        assert self._run_predict("gas cylinder") == "utilities"

    def test_predict_other(self):
        assert self._run_predict("movie tickets") == "other"

    def test_predict_other_pizza(self):
        assert self._run_predict("pizza dinner") == "other"

    def test_predict_case_insensitive(self):
        assert self._run_predict("RENT") == "rent"
        assert self._run_predict("Electric Bill") == "electricity"

    def test_keyword_rules_covers_all_categories(self):
        result = _run_isolated(
            "from smart_suggest import KEYWORD_RULES\n"
            "cats = {cat for _, cat in KEYWORD_RULES}\n"
            "assert cats == {'rent','electricity','groceries','utilities'}\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_keyword_rules_non_empty(self):
        result = _run_isolated(
            "from smart_suggest import KEYWORD_RULES\n"
            "assert len(KEYWORD_RULES) >= 4\n"
            "for keywords, cat in KEYWORD_RULES:\n"
            "    assert len(keywords) > 0, f'Empty keywords for {cat}'\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr


# ── Balance Engine Tests ────────────────────────────────────────


class TestBalanceEngine:
    """Test balance_engine.py imports and function signatures."""

    def test_imports(self):
        result = _run_isolated(
            "from balance_engine import compute_room_balances, get_user_balance\n"
            "assert callable(compute_room_balances)\n"
            "assert callable(get_user_balance)\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_compute_room_balances_empty(self):
        result = _run_isolated(
            "from unittest.mock import MagicMock\n"
            "from balance_engine import compute_room_balances\n"
            "db = MagicMock()\n"
            "db.query.return_value.filter.return_value.all.return_value = []\n"
            "balances = compute_room_balances(1, db)\n"
            "assert balances == []\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr


# ── Service Function Tests ──────────────────────────────────────


class TestExpenseServiceImports:
    """Test that expense service module imports work."""

    def test_service_imports(self):
        result = _run_isolated(
            "from service import (\n"
            "    create_expense, get_room_expenses,\n"
            "    get_expense_by_id, delete_expense, settle_my_split\n"
            ")\n"
            "assert callable(create_expense)\n"
            "assert callable(get_room_expenses)\n"
            "assert callable(get_expense_by_id)\n"
            "assert callable(delete_expense)\n"
            "assert callable(settle_my_split)\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_router_imports(self):
        result = _run_isolated(
            "from router import router\n"
            "assert router.prefix == '/expenses'\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_main_app_exists(self):
        result = _run_isolated(
            "from main import app\n"
            "assert app.title == 'Flatmate – Expense Service'\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr


# ── Route Tests ─────────────────────────────────────────────────


class TestExpenseRoutes:
    """Verify expense router has all required routes."""

    def test_has_create_route(self):
        source = _read_source('router.py')
        assert '@router.post(' in source and 'response_model=ExpenseOut' in source

    def test_has_suggest_category_route(self):
        assert '/suggest/category' in _read_source('router.py')

    def test_has_suggest_recurring_route(self):
        assert '/suggest/recurring/{room_id}' in _read_source('router.py')

    def test_has_room_balance_route(self):
        assert '/balance/room/{room_id}' in _read_source('router.py')

    def test_has_my_balance_route(self):
        assert '/balance/me/room/{room_id}' in _read_source('router.py')

    def test_has_list_room_expenses_route(self):
        assert '/room/{room_id}' in _read_source('router.py')

    def test_has_get_expense_route(self):
        assert '/{expense_id}' in _read_source('router.py')

    def test_has_delete_expense_route(self):
        assert '@router.delete(' in _read_source('router.py')

    def test_has_settle_route(self):
        assert '@router.patch(' in _read_source('router.py') and 'settle' in _read_source('router.py')

    def test_fixed_paths_before_parameterized(self):
        source = _read_source('router.py')
        lines = source.split('\n')
        fixed_lines = []
        param_lines = []
        for i, line in enumerate(lines):
            if '@router.' in line:
                if '/{expense_id}' in line:
                    param_lines.append(i)
                else:
                    fixed_lines.append(i)
        if fixed_lines and param_lines:
            assert max(fixed_lines) < min(param_lines), \
                "Fixed paths must come before parameterized paths"

    def test_uses_auth_dependency(self):
        assert 'get_current_user_id' in _read_source('router.py')

    def test_uses_db_dependency(self):
        assert 'get_db' in _read_source('router.py')
