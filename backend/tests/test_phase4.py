"""Phase 4 Tests — Payment Service: models, schemas, service logic, routes."""

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
    'SERVICE_NAME': 'payment-service',
}


def _read_source(filename: str) -> str:
    path = os.path.join(SERVICES, 'payment-service', 'src', filename)
    with open(path) as f:
        return f.read()


def _run_isolated(test_code: str):
    src_dir = os.path.join(SERVICES, 'payment-service', 'src')
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


class TestPaymentModels:
    """Verify payment-service models via source code analysis."""

    def test_payment_tablename(self):
        assert '__tablename__ = "payments"' in _read_source('models.py')

    def test_has_required_columns(self):
        source = _read_source('models.py')
        for col in ['id', 'room_id', 'from_user', 'to_user', 'amount', 'status', 'upi_ref', 'note', 'created_at', 'settled_at']:
            assert col in source, f"Missing column: {col}"

    def test_from_user_references_profiles(self):
        assert 'ForeignKey("profiles.id")' in _read_source('models.py')

    def test_to_user_references_profiles(self):
        source = _read_source('models.py')
        assert source.count('ForeignKey("profiles.id")') == 2, "from_user and to_user should both reference profiles"

    def test_room_id_references_rooms(self):
        assert 'ForeignKey("rooms.id")' in _read_source('models.py')

    def test_has_status_enum(self):
        source = _read_source('models.py')
        assert '"pending"' in source
        assert '"settled"' in source

    def test_has_payment_status_enum_name(self):
        assert 'name="payment_status"' in _read_source('models.py')

    def test_imports_from_database(self):
        assert 'from database import Base' in _read_source('models.py')

    def test_has_numeric_amount(self):
        assert 'Numeric(12, 2)' in _read_source('models.py')


# ── Schema Tests ────────────────────────────────────────────────


class TestPaymentSchemas:
    """Test payment-service schemas via isolated import."""

    def test_payment_create(self):
        result = _run_isolated(
            "from decimal import Decimal\n"
            "from schemas import PaymentCreate\n"
            "p = PaymentCreate(room_id=1, to_user='uuid', amount=Decimal('500.00'))\n"
            "assert p.amount == Decimal('500.00')\n"
            "assert p.upi_ref is None\n"
            "assert p.note is None\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_payment_create_with_upi_ref(self):
        result = _run_isolated(
            "from decimal import Decimal\n"
            "from schemas import PaymentCreate\n"
            "p = PaymentCreate(room_id=1, to_user='uuid', amount=Decimal('1000.00'),\n"
            "    upi_ref='UPI123456', note='rent payment')\n"
            "assert p.upi_ref == 'UPI123456'\n"
            "assert p.note == 'rent payment'\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_payment_create_invalid_amount(self):
        result = _run_isolated(
            "from decimal import Decimal\n"
            "from pydantic import ValidationError\n"
            "from schemas import PaymentCreate\n"
            "try:\n"
            "    PaymentCreate(room_id=1, to_user='uuid', amount=Decimal('-100'))\n"
            "    assert False, 'Should have raised'\n"
            "except ValidationError:\n"
            "    print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_payment_create_zero_amount(self):
        result = _run_isolated(
            "from decimal import Decimal\n"
            "from pydantic import ValidationError\n"
            "from schemas import PaymentCreate\n"
            "try:\n"
            "    PaymentCreate(room_id=1, to_user='uuid', amount=Decimal('0'))\n"
            "    assert False, 'Should have raised'\n"
            "except ValidationError:\n"
            "    print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_payment_settle_optional(self):
        result = _run_isolated(
            "from schemas import PaymentSettle\n"
            "p = PaymentSettle()\n"
            "assert p.upi_ref is None\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_payment_settle_with_upi(self):
        result = _run_isolated(
            "from schemas import PaymentSettle\n"
            "p = PaymentSettle(upi_ref='REF123')\n"
            "assert p.upi_ref == 'REF123'\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_payment_out_fields(self):
        result = _run_isolated(
            "from schemas import PaymentOut\n"
            "f = PaymentOut.model_fields\n"
            "expected = ['id','room_id','from_user','to_user','amount','status','upi_ref','note','created_at','settled_at']\n"
            "assert all(k in f for k in expected), f'Missing: {[k for k in expected if k not in f]}'\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_payment_summary_fields(self):
        result = _run_isolated(
            "from schemas import PaymentSummary\n"
            "f = PaymentSummary.model_fields\n"
            "expected = ['total_paid','total_received','pending_out','pending_in','transaction_count']\n"
            "assert all(k in f for k in expected)\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_payment_out_from_attributes(self):
        result = _run_isolated(
            "from schemas import PaymentOut\n"
            "assert PaymentOut.model_config.get('from_attributes') is True\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr


# ── Service Function Tests ──────────────────────────────────────


class TestPaymentServiceImports:
    """Test that payment service module imports work."""

    def test_service_imports(self):
        result = _run_isolated(
            "from service import (\n"
            "    create_payment, settle_payment, get_payment_by_id,\n"
            "    get_my_payments, get_room_payments, get_my_summary\n"
            ")\n"
            "assert callable(create_payment)\n"
            "assert callable(settle_payment)\n"
            "assert callable(get_payment_by_id)\n"
            "assert callable(get_my_payments)\n"
            "assert callable(get_room_payments)\n"
            "assert callable(get_my_summary)\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_router_imports(self):
        result = _run_isolated(
            "from router import router\n"
            "assert router.prefix == '/payments'\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_main_app_exists(self):
        result = _run_isolated(
            "from main import app\n"
            "assert app.title == 'Flatmate – Payment Service'\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr


class TestPaymentServiceLogic:
    """Test payment service business logic via isolated code."""

    def test_create_payment_self_raises(self):
        result = _run_isolated(
            "from decimal import Decimal\n"
            "from unittest.mock import MagicMock\n"
            "from fastapi import HTTPException\n"
            "from schemas import PaymentCreate\n"
            "from service import create_payment\n"
            "db = MagicMock()\n"
            "data = PaymentCreate(room_id=1, to_user='same-user', amount=Decimal('100'))\n"
            "try:\n"
            "    create_payment(data, 'same-user', db)\n"
            "    assert False, 'Should have raised'\n"
            "except HTTPException as e:\n"
            "    assert e.status_code == 400\n"
            "    print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_settle_payment_not_found(self):
        result = _run_isolated(
            "from unittest.mock import MagicMock\n"
            "from fastapi import HTTPException\n"
            "from service import settle_payment\n"
            "db = MagicMock()\n"
            "db.query.return_value.filter.return_value.first.return_value = None\n"
            "try:\n"
            "    settle_payment(999, 'user1', None, db)\n"
            "    assert False, 'Should have raised'\n"
            "except HTTPException as e:\n"
            "    assert e.status_code == 404\n"
            "    print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_settle_payment_wrong_user(self):
        result = _run_isolated(
            "from unittest.mock import MagicMock\n"
            "from fastapi import HTTPException\n"
            "from service import settle_payment\n"
            "db = MagicMock()\n"
            "mock_payment = MagicMock()\n"
            "mock_payment.to_user = 'recipient-uuid'\n"
            "db.query.return_value.filter.return_value.first.return_value = mock_payment\n"
            "try:\n"
            "    settle_payment(1, 'wrong-user', None, db)\n"
            "    assert False, 'Should have raised'\n"
            "except HTTPException as e:\n"
            "    assert e.status_code == 403\n"
            "    print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_settle_already_settled(self):
        result = _run_isolated(
            "from unittest.mock import MagicMock\n"
            "from fastapi import HTTPException\n"
            "from service import settle_payment\n"
            "db = MagicMock()\n"
            "mock_payment = MagicMock()\n"
            "mock_payment.to_user = 'user1'\n"
            "mock_payment.status = 'settled'\n"
            "db.query.return_value.filter.return_value.first.return_value = mock_payment\n"
            "try:\n"
            "    settle_payment(1, 'user1', None, db)\n"
            "    assert False, 'Should have raised'\n"
            "except HTTPException as e:\n"
            "    assert e.status_code == 409\n"
            "    print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_get_payment_not_found(self):
        result = _run_isolated(
            "from unittest.mock import MagicMock\n"
            "from fastapi import HTTPException\n"
            "from service import get_payment_by_id\n"
            "db = MagicMock()\n"
            "db.query.return_value.filter.return_value.first.return_value = None\n"
            "try:\n"
            "    get_payment_by_id(999, db)\n"
            "    assert False, 'Should have raised'\n"
            "except HTTPException as e:\n"
            "    assert e.status_code == 404\n"
            "    print('PASS')"
        )
        assert result.returncode == 0, result.stderr

    def test_get_my_summary_calculates(self):
        result = _run_isolated(
            "from decimal import Decimal\n"
            "from unittest.mock import MagicMock, patch\n"
            "from schemas import PaymentSummary\n"
            "from service import get_my_summary\n"
            "db = MagicMock()\n"
            "user_id = 'user1'\n"
            "p1 = MagicMock()\n"
            "p1.from_user = user_id\n"
            "p1.to_user = 'u2'\n"
            "p1.amount = Decimal('100')\n"
            "p1.status = 'settled'\n"
            "p2 = MagicMock()\n"
            "p2.from_user = 'u3'\n"
            "p2.to_user = user_id\n"
            "p2.amount = Decimal('50')\n"
            "p2.status = 'settled'\n"
            "p3 = MagicMock()\n"
            "p3.from_user = user_id\n"
            "p3.to_user = 'u4'\n"
            "p3.amount = Decimal('30')\n"
            "p3.status = 'pending'\n"
            "with patch('service.get_my_payments', return_value=[p1, p2, p3]):\n"
            "    summary = get_my_summary(user_id, db)\n"
            "assert summary.total_paid == 100.0\n"
            "assert summary.total_received == 50.0\n"
            "assert summary.pending_out == 30.0\n"
            "assert summary.pending_in == 0.0\n"
            "assert summary.transaction_count == 3\n"
            "print('PASS')"
        )
        assert result.returncode == 0, result.stderr


# ── Route Tests ─────────────────────────────────────────────────


class TestPaymentRoutes:
    """Verify payment router has all required routes."""

    def test_has_create_route(self):
        source = _read_source('router.py')
        assert '@router.post(' in source and 'response_model=PaymentOut' in source

    def test_has_me_route(self):
        assert '@router.get("/me"' in _read_source('router.py')

    def test_has_me_summary_route(self):
        assert '/me/summary' in _read_source('router.py')

    def test_has_room_payments_route(self):
        assert '/room/{room_id}' in _read_source('router.py')

    def test_has_settle_route(self):
        assert '@router.patch(' in _read_source('router.py') and 'settle' in _read_source('router.py')

    def test_has_get_payment_route(self):
        assert '@router.get("/{payment_id}"' in _read_source('router.py')

    def test_fixed_paths_before_parameterized(self):
        source = _read_source('router.py')
        lines = source.split('\n')
        fixed_lines = []
        param_lines = []
        for i, line in enumerate(lines):
            if '@router.' in line:
                if '/{payment_id}' in line:
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

    def test_me_before_parameterized(self):
        source = _read_source('router.py')
        lines = source.split('\n')
        me_idx = next((i for i, l in enumerate(lines) if '/me' in l and '@router.' in l), None)
        param_idx = next((i for i, l in enumerate(lines) if '/{payment_id}' in l and '@router.' in l), None)
        assert me_idx is not None, "No /me route found"
        assert param_idx is not None, "No parameterized route found"
        assert me_idx < param_idx, "/me must come before parameterized routes"


# ── Integration: Payment + Expense Connection ───────────────────


class TestPaymentExpenseIntegration:
    """Verify payment-service references are consistent with expense-service."""

    def test_payment_model_has_room_id(self):
        source = _read_source('models.py')
        assert 'room_id' in source

    def test_payment_model_has_from_user(self):
        source = _read_source('models.py')
        assert 'from_user' in source

    def test_payment_model_has_to_user(self):
        source = _read_source('models.py')
        assert 'to_user' in source

    def test_payment_status_pending_default(self):
        source = _read_source('models.py')
        assert 'default="pending"' in source
