"""Phase 2 Tests — User & Room Services: models, schemas, service logic.

Uses subprocess isolation for each service to avoid SQLAlchemy metadata conflicts.
Pure logic tests (split calculator, smart suggest) run in-process.
"""

import ast
import os
import subprocess
import sys
from decimal import Decimal
from unittest.mock import patch

SHARED = os.path.join(os.path.dirname(__file__), '..', 'shared')
SERVICES = os.path.join(os.path.dirname(__file__), '..', 'services')

ENV = {
    **os.environ,
    'DB_HOST': 'localhost',
    'DB_NAME': 'postgres',
    'DB_USER': 'postgres',
    'DB_PASSWORD': 'test',
    'SUPABASE_URL': 'https://test.supabase.co',
    'SUPABASE_SERVICE_KEY': 'test-key',
    'SUPABASE_JWT_SECRET': 'test-secret',
    'ENVIRONMENT': 'development',
    'SERVICE_NAME': 'test',
}


def _read_source(service: str, filename: str) -> str:
    path = os.path.join(SERVICES, service, 'src', filename)
    with open(path) as f:
        return f.read()


def _run_isolated(service: str, test_code: str):
    """Run test code in a subprocess with the service's src on sys.path."""
    src_dir = os.path.join(SERVICES, service, 'src')
    code = (
        f"import sys; sys.path.insert(0, {SHARED!r}); sys.path.insert(0, {src_dir!r})\n"
        + test_code
    )
    result = subprocess.run(
        [sys.executable, '-c', code],
        capture_output=True, text=True, env=ENV, timeout=10,
    )
    return result


# ── Schema Source Code Analysis ─────────────────────────────────


class TestUserModelsSource:
    """Verify user-service models via source code analysis."""

    def test_tablename_is_profiles(self):
        source = _read_source('user-service', 'models.py')
        assert '__tablename__ = "profiles"' in source

    def test_has_uuid_primary_key(self):
        source = _read_source('user-service', 'models.py')
        assert 'UUID(as_uuid=True)' in source
        assert 'primary_key=True' in source

    def test_has_required_columns(self):
        source = _read_source('user-service', 'models.py')
        for col in ['name', 'email', 'upi_id', 'phone', 'avatar_key', 'created_at', 'updated_at']:
            assert col in source, f"Missing column: {col}"

    def test_imports_from_database(self):
        source = _read_source('user-service', 'models.py')
        assert 'from database import Base' in source

    def test_no_users_table(self):
        source = _read_source('user-service', 'models.py')
        assert '__tablename__ = "users"' not in source


class TestRoomModelsSource:
    """Verify room-service models via source code analysis."""

    def test_room_tablename(self):
        source = _read_source('room-service', 'models.py')
        assert '__tablename__ = "rooms"' in source

    def test_room_member_tablename(self):
        source = _read_source('room-service', 'models.py')
        assert '__tablename__ = "room_members"' in source

    def test_created_by_references_profiles(self):
        source = _read_source('room-service', 'models.py')
        assert 'ForeignKey("profiles.id")' in source

    def test_user_id_references_profiles(self):
        source = _read_source('room-service', 'models.py')
        assert 'ForeignKey("profiles.id", ondelete="CASCADE")' in source


class TestExpenseModelsSource:
    """Verify expense-service models via source code analysis."""

    def test_expense_tablename(self):
        source = _read_source('expense-service', 'models.py')
        assert '__tablename__ = "expenses"' in source

    def test_expense_split_tablename(self):
        source = _read_source('expense-service', 'models.py')
        assert '__tablename__ = "expense_splits"' in source

    def test_paid_by_references_profiles(self):
        source = _read_source('expense-service', 'models.py')
        assert 'ForeignKey("profiles.id")' in source

    def test_has_split_type_enum(self):
        source = _read_source('expense-service', 'models.py')
        assert '"equal"' in source
        assert '"custom"' in source
        assert '"percentage"' in source


class TestPaymentModelsSource:
    """Verify payment-service models via source code analysis."""

    def test_payment_tablename(self):
        source = _read_source('payment-service', 'models.py')
        assert '__tablename__ = "payments"' in source

    def test_from_user_references_profiles(self):
        source = _read_source('payment-service', 'models.py')
        assert 'ForeignKey("profiles.id")' in source

    def test_has_status_enum(self):
        source = _read_source('payment-service', 'models.py')
        assert '"pending"' in source
        assert '"settled"' in source


# ── Schema Tests (isolated per service) ─────────────────────────


class TestUserSchemas:
    """Test user-service schemas via isolated import."""

    def test_user_create(self):
        result = _run_isolated('user-service',
            "from schemas import UserCreate; "
            "u = UserCreate(name='Test', email='test@example.com'); "
            "assert u.name == 'Test'; "
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_user_create_invalid_email(self):
        result = _run_isolated('user-service',
            "from pydantic import ValidationError\n"
            "from schemas import UserCreate\n"
            "try:\n"
            "    UserCreate(name='Test', email='not-email')\n"
            "    assert False, 'Should have raised'\n"
            "except ValidationError:\n"
            "    print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_user_update_optional(self):
        result = _run_isolated('user-service',
            "from schemas import UserUpdate; "
            "u = UserUpdate(); "
            "assert u.name is None; "
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_user_out_has_avatar_url(self):
        result = _run_isolated('user-service',
            "from schemas import UserOut; "
            "assert 'avatar_url' in UserOut.model_fields; "
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr


class TestRoomSchemas:
    """Test room-service schemas via isolated import."""

    def test_room_join_uppercase(self):
        result = _run_isolated('room-service',
            "from schemas import RoomJoin; "
            "j = RoomJoin(room_code='k7xq2wrp'); "
            "assert j.room_code == 'K7XQ2WRP'; "
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_room_out_fields(self):
        result = _run_isolated('room-service',
            "from schemas import RoomOut; "
            "f = RoomOut.model_fields; "
            "assert 'id' in f and 'room_code' in f and 'created_by' in f; "
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr


class TestRoomServiceLogic:
    """Test room-service code generation."""

    def test_generate_room_code_length(self):
        result = _run_isolated('room-service',
            "from service import _generate_room_code; "
            "code = _generate_room_code(); "
            "assert len(code) == 8, f'Expected 8, got {len(code)}'; "
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_generate_room_code_uppercase(self):
        result = _run_isolated('room-service',
            "from service import _generate_room_code; "
            "code = _generate_room_code(); "
            "assert code == code.upper(); "
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_generate_room_code_unique(self):
        result = _run_isolated('room-service',
            "from service import _generate_room_code; "
            "codes = {_generate_room_code() for _ in range(20)}; "
            "assert len(codes) == 20, f'Only {len(codes)} unique codes'; "
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr


# ── Split Calculator Tests (isolated in expense-service) ────────


class TestSplitCalculator:
    """Test split_calculator.py logic via isolated import."""

    def test_equal_split_basic(self):
        result = _run_isolated('expense-service',
            "from decimal import Decimal; "
            "from schemas import ExpenseCreate; "
            "from split_calculator import calculate_splits; "
            "data = ExpenseCreate(room_id=1, title='E', amount=Decimal('2400.00'), "
            "category='electricity', split_type='equal', "
            "members=['u1','u2','u3','u4']); "
            "splits = calculate_splits(data); "
            "assert len(splits) == 4; "
            "assert all(s['amount'] == 600.00 for s in splits); "
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_equal_split_rounding(self):
        result = _run_isolated('expense-service',
            "from decimal import Decimal; "
            "from schemas import ExpenseCreate; "
            "from split_calculator import calculate_splits; "
            "data = ExpenseCreate(room_id=1, title='G', amount=Decimal('100.00'), "
            "split_type='equal', members=['a','b','c']); "
            "splits = calculate_splits(data); "
            "total = sum(Decimal(str(s['amount'])) for s in splits); "
            "assert total == Decimal('100.00'), f'Total was {total}'; "
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_equal_split_last_person_fixes_remainder(self):
        result = _run_isolated('expense-service',
            "from decimal import Decimal; "
            "from schemas import ExpenseCreate; "
            "from split_calculator import calculate_splits; "
            "data = ExpenseCreate(room_id=1, title='B', amount=Decimal('100.00'), "
            "split_type='equal', members=['a','b','c']); "
            "splits = calculate_splits(data); "
            "amounts = [s['amount'] for s in splits]; "
            "# 100/3 = 33.33, 33.33, last gets 33.34 to make total 100 "
            "assert amounts[0] == 33.33; "
            "assert amounts[1] == 33.33; "
            "assert amounts[2] == 33.34; "
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_custom_split(self):
        result = _run_isolated('expense-service',
            "from decimal import Decimal; "
            "from schemas import ExpenseCreate; "
            "from split_calculator import calculate_splits; "
            "data = ExpenseCreate(room_id=1, title='C', amount=Decimal('100.00'), "
            "split_type='custom', members=['a','b'], "
            "splits=[{'user_id':'a','amount':Decimal('70')},"
            "{'user_id':'b','amount':'30'}]); "
            "splits = calculate_splits(data); "
            "assert len(splits) == 2; "
            "assert splits[0]['amount'] == 70.00; "
            "assert splits[1]['amount'] == 30.00; "
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_percentage_split(self):
        result = _run_isolated('expense-service',
            "from decimal import Decimal; "
            "from schemas import ExpenseCreate; "
            "from split_calculator import calculate_splits; "
            "data = ExpenseCreate(room_id=1, title='P', amount=Decimal('1000.00'), "
            "split_type='percentage', members=['a','b'], "
            "splits=[{'user_id':'a','amount':Decimal('60')},"
            "{'user_id':'b','amount':'40'}]); "
            "splits = calculate_splits(data); "
            "assert len(splits) == 2; "
            "assert splits[0]['amount'] == 600.00; "
            "assert splits[1]['amount'] == 400.00; "
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr


# ── Smart Suggest Tests (isolated in expense-service) ───────────


class TestSmartSuggest:
    """Test smart_suggest.py logic via isolated import."""

    def _run_predict(self, title):
        result = _run_isolated('expense-service',
            f"from smart_suggest import predict_category; "
            f"r = predict_category({title!r}); "
            f"print(r)"
        )
        assert result.returncode == 0, result.stderr
        return result.stdout.strip()

    def test_predict_rent(self):
        assert self._run_predict("rent for april") == "rent"

    def test_predict_electricity(self):
        assert self._run_predict("MSEDCL power bill") == "electricity"

    def test_predict_groceries(self):
        assert self._run_predict("bigbasket order") == "groceries"

    def test_predict_utilities(self):
        assert self._run_predict("jio wifi bill") == "utilities"

    def test_predict_other(self):
        assert self._run_predict("movie tickets") == "other"

    def test_keyword_rules_covers_all_categories(self):
        result = _run_isolated('expense-service',
            "from smart_suggest import KEYWORD_RULES; "
            "cats = {cat for _, cat in KEYWORD_RULES}; "
            "assert cats == {'rent','electricity','groceries','utilities'}; "
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr


# ── Payment Schema Tests (isolated) ────────────────────────────


class TestPaymentSchemas:
    """Test payment-service schemas via isolated import."""

    def test_payment_create(self):
        result = _run_isolated('payment-service',
            "from decimal import Decimal; "
            "from schemas import PaymentCreate; "
            "p = PaymentCreate(room_id=1, to_user='uuid', amount=Decimal('500.00')); "
            "assert p.amount == Decimal('500.00'); "
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_payment_summary_fields(self):
        result = _run_isolated('payment-service',
            "from schemas import PaymentSummary; "
            "f = PaymentSummary.model_fields; "
            "assert all(k in f for k in ['total_paid','total_received','pending_out','pending_in']); "
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr


# ── Health Endpoint Tests ───────────────────────────────────────


class TestHealthEndpoints:
    """Test that all services have /health route via source."""

    def test_user_service_health(self):
        source = _read_source('user-service', 'main.py')
        assert '@app.get("/health")' in source

    def test_room_service_health(self):
        source = _read_source('room-service', 'main.py')
        assert '@app.get("/health")' in source

    def test_expense_service_health(self):
        source = _read_source('expense-service', 'main.py')
        assert '@app.get("/health")' in source

    def test_payment_service_health(self):
        source = _read_source('payment-service', 'main.py')
        assert '@app.get("/health")' in source


# ── Route Ordering Tests ────────────────────────────────────────


class TestRouteOrdering:
    """Verify fixed paths are before parameterized paths in routers."""

    def _get_routes(self, service):
        source = _read_source(service, 'router.py')
        lines = source.split('\n')
        route_lines = []
        for i, line in enumerate(lines):
            if '@router.' in line and ('get(' in line or 'post(' in line or 'patch(' in line or 'delete(' in line):
                route_lines.append((i, line.strip()))
        return route_lines

    def test_expense_router_suggest_before_id(self):
        routes = self._get_routes('expense-service')
        suggest_idx = next(i for i, l in routes if '/suggest/' in l)
        param_idx = next(i for i, l in routes if '/{expense_id}' in l)
        assert suggest_idx < param_idx, "Suggest routes must be before parameterized /{expense_id}"

    def test_expense_router_balance_before_id(self):
        routes = self._get_routes('expense-service')
        balance_idx = next(i for i, l in routes if '/balance/' in l)
        param_idx = next(i for i, l in routes if '/{expense_id}' in l)
        assert balance_idx < param_idx, "Balance routes must be before parameterized /{expense_id}"

    def test_payment_router_me_before_id(self):
        routes = self._get_routes('payment-service')
        me_idx = next(i for i, l in routes if '/me' in l)
        param_idx = next(i for i, l in routes if '/{payment_id}' in l)
        assert me_idx < param_idx, "/me routes must be before parameterized /{payment_id}"

    def test_room_router_mine_before_id(self):
        routes = self._get_routes('room-service')
        mine_idx = next(i for i, l in routes if '/mine' in l)
        param_idx = next(i for i, l in routes if '/{room_id}' in l)
        assert mine_idx < param_idx, "/mine must be before /{room_id}"
