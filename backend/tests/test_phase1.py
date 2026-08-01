"""Phase 1 Tests — Foundation: Schema, Config, Auth, Cache."""

import os
import sys

# Add shared and service src directories to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))


class TestSchemaSQL:
    """Validate the Supabase schema file."""

    def setup_method(self):
        schema_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'supabase', 'schema.sql'
        )
        with open(schema_path) as f:
            self.schema = f.read()

    def test_has_extensions(self):
        assert 'CREATE EXTENSION' in self.schema
        assert 'pgcrypto' in self.schema

    def test_has_enums(self):
        assert 'expense_category' in self.schema
        assert 'split_type' in self.schema
        assert 'payment_status' in self.schema
        assert 'member_role' in self.schema

    def test_has_profiles_table(self):
        assert 'CREATE TABLE profiles' in self.schema
        assert 'UUID PRIMARY KEY' in self.schema
        assert 'REFERENCES auth.users(id)' in self.schema

    def test_has_rooms_table(self):
        assert 'CREATE TABLE rooms' in self.schema
        assert 'room_code' in self.schema
        assert 'created_by' in self.schema

    def test_has_room_members_table(self):
        assert 'CREATE TABLE room_members' in self.schema
        assert 'member_role' in self.schema

    def test_has_expenses_table(self):
        assert 'CREATE TABLE expenses' in self.schema
        assert 'expense_category' in self.schema
        assert 'split_type' in self.schema
        assert 'paid_by' in self.schema

    def test_has_expense_splits_table(self):
        assert 'CREATE TABLE expense_splits' in self.schema
        assert 'is_settled' in self.schema
        assert 'settled_at' in self.schema

    def test_has_payments_table(self):
        assert 'CREATE TABLE payments' in self.schema
        assert 'payment_status' in self.schema
        assert 'from_user' in self.schema
        assert 'to_user' in self.schema
        assert 'no_self_payment' in self.schema

    def test_has_indexes(self):
        assert 'idx_profiles_email' in self.schema
        assert 'idx_room_members_room' in self.schema
        assert 'idx_expenses_room' in self.schema
        assert 'idx_splits_expense' in self.schema
        assert 'idx_payments_room' in self.schema

    def test_has_rls(self):
        assert 'ENABLE ROW LEVEL SECURITY' in self.schema
        assert 'profiles_select_all' in self.schema
        assert 'rooms_select_members_only' in self.schema

    def test_has_storage_buckets(self):
        assert "storage.buckets" in self.schema
        assert "'avatars'" in self.schema
        assert "'receipts'" in self.schema

    def test_has_triggers(self):
        assert 'handle_new_user' in self.schema
        assert 'on_auth_user_created' in self.schema
        assert 'update_updated_at' in self.schema
        assert 'profiles_updated_at' in self.schema

    def test_no_cognito_references(self):
        """Schema should not reference Cognito anywhere."""
        lower = self.schema.lower()
        assert 'cognito' not in lower

    def test_references_profiles_not_users(self):
        """User-referencing FKs should use profiles, not a 'users' table."""
        lines = [l for l in self.schema.split('\n') if 'REFERENCES' in l]
        for line in lines:
            # Allow auth.users (Supabase auth table) and self-references like rooms(id)
            if 'auth.users' in line:
                continue
            # Skip FKs that reference other non-user tables (rooms, expenses, etc.)
            if 'rooms(id)' in line or 'expenses(id)' in line:
                continue
            # If it looks like a user ID FK, it should reference profiles
            if 'user_id' in line or 'paid_by' in line or 'from_user' in line or 'to_user' in line or 'created_by' in line:
                assert 'profiles(id)' in line, f"User FK should reference profiles(id): {line}"


class TestConfig:
    """Test config.py loads correctly with Supabase settings."""

    def test_config_reads_env_vars(self):
        """Verify Settings model has all required Supabase fields."""
        # We can't instantiate Settings without env vars, but we can check the model
        from pydantic import Field
        # Import the module without instantiating
        import importlib
        import config as config_mod
        importlib.reload(config_mod)

        fields = config_mod.Settings.model_fields
        expected_fields = [
            'supabase_url', 'supabase_service_key', 'supabase_jwt_secret',
            'environment', 'service_name',
        ]
        for field_name in expected_fields:
            assert field_name in fields, f"Missing field: {field_name}"

    def test_no_cognito_in_config(self):
        """Config should not have Cognito settings."""
        import config as config_mod
        fields = config_mod.Settings.model_fields
        for field_name in fields:
            assert 'cognito' not in field_name.lower(), f"Cognito field found: {field_name}"

    def test_no_redis_in_config(self):
        """Config should not have Redis settings."""
        import config as config_mod
        fields = config_mod.Settings.model_fields
        for field_name in fields:
            assert 'redis' not in field_name.lower(), f"Redis field found: {field_name}"

    def test_no_s3_in_config(self):
        """Config should not have S3 settings."""
        import config as config_mod
        fields = config_mod.Settings.model_fields
        for field_name in fields:
            assert 's3' not in field_name.lower(), f"S3 field found: {field_name}"

    def test_db_url_property(self):
        """Test db_url property derives connection string from Supabase URL."""
        import config as config_mod

        mock_settings = config_mod.Settings(
            supabase_url='https://abc123.supabase.co',
            supabase_service_key='test-key',
            supabase_jwt_secret='test-secret',
        )
        url = mock_settings.db_url
        assert url == 'postgresql+psycopg2://postgres:test-key@db.abc123.supabase.co:5432/postgres'


class TestAuth:
    """Test Supabase JWT verification."""

    def test_verify_supabase_token_import(self):
        """Verify auth module imports correctly."""
        from auth import verify_supabase_token, get_current_user_id
        assert callable(verify_supabase_token)
        assert callable(get_current_user_id)

    def test_invalid_token_raises_401(self):
        """Invalid token should raise HTTPException 401."""
        from auth import verify_supabase_token
        from fastapi import HTTPException
        import pytest

        with pytest.raises(HTTPException) as exc_info:
            verify_supabase_token("invalid.token.here")
        assert exc_info.value.status_code == 401

    def test_empty_token_raises_401(self):
        """Empty token should raise HTTPException 401."""
        from auth import verify_supabase_token
        from fastapi import HTTPException
        import pytest

        with pytest.raises(HTTPException) as exc_info:
            verify_supabase_token("")
        assert exc_info.value.status_code == 401

    def test_malformed_token_raises_401(self):
        """Malformed token should raise HTTPException 401."""
        from auth import verify_supabase_token
        from fastapi import HTTPException
        import pytest

        with pytest.raises(HTTPException) as exc_info:
            verify_supabase_token("not-a-jwt")
        assert exc_info.value.status_code == 401

    def test_no_cognito_jwks_import(self):
        """Auth module should not import Cognito JWKS."""
        import auth
        import inspect
        source = inspect.getsource(auth)
        assert 'cognito' not in source.lower()
        assert 'jwks' not in source.lower()
        assert 'RS256' not in source


class TestCache:
    """Test cache.py no-op implementation."""

    def test_cache_set_is_noop(self):
        """cache_set should not raise."""
        from cache import cache_set
        cache_set("key", "value")

    def test_cache_get_returns_none(self):
        """cache_get should always return None."""
        from cache import cache_get
        result = cache_get("key")
        assert result is None

    def test_cache_delete_is_noop(self):
        """cache_delete should not raise."""
        from cache import cache_delete
        cache_delete("key")

    def test_cache_delete_pattern_is_noop(self):
        """cache_delete_pattern should not raise."""
        from cache import cache_delete_pattern
        cache_delete_pattern("key:*")


class TestSupabaseClient:
    """Test supabase_client module."""

    def test_import(self):
        """Verify supabase_client module imports."""
        from supabase_client import get_supabase
        assert callable(get_supabase)


class TestEnvFiles:
    """Test .env files exist and have correct structure."""

    def setup_method(self):
        self.services = ['user-service', 'room-service', 'expense-service', 'payment-service']

    def test_env_files_exist(self):
        """All 4 services should have .env files."""
        for service in self.services:
            env_path = os.path.join(
                os.path.dirname(__file__), '..', 'services', service, '.env'
            )
            assert os.path.exists(env_path), f"Missing .env for {service}"

    def test_env_files_have_supabase_vars(self):
        """All .env files should have Supabase variables."""
        for service in self.services:
            env_path = os.path.join(
                os.path.dirname(__file__), '..', 'services', service, '.env'
            )
            with open(env_path) as f:
                content = f.read()
            assert 'SUPABASE_URL' in content, f"{service} missing SUPABASE_URL"
            assert 'SUPABASE_SERVICE_KEY' in content, f"{service} missing SUPABASE_SERVICE_KEY"
            assert 'SUPABASE_JWT_SECRET' in content, f"{service} missing SUPABASE_JWT_SECRET"

    def test_env_files_no_db_vars(self):
        """All .env files should NOT have database variables (derived from Supabase URL)."""
        for service in self.services:
            env_path = os.path.join(
                os.path.dirname(__file__), '..', 'services', service, '.env'
            )
            with open(env_path) as f:
                content = f.read()
            assert 'DB_HOST' not in content, f"{service} should not have DB_HOST"
            assert 'DB_PASSWORD' not in content, f"{service} should not have DB_PASSWORD"

    def test_env_files_no_cognito(self):
        """No .env file should reference Cognito."""
        for service in self.services:
            env_path = os.path.join(
                os.path.dirname(__file__), '..', 'services', service, '.env'
            )
            with open(env_path) as f:
                content = f.read().lower()
            assert 'cognito' not in content, f"{service} .env references Cognito"

    def test_env_files_no_redis(self):
        """No .env file should reference Redis."""
        for service in self.services:
            env_path = os.path.join(
                os.path.dirname(__file__), '..', 'services', service, '.env'
            )
            with open(env_path) as f:
                content = f.read().lower()
            assert 'redis' not in content, f"{service} .env references Redis"
