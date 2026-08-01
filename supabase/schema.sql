-- ================================================================
-- Flatmate — Supabase Database Schema
-- Run this entire file in Supabase Dashboard → SQL Editor
-- ================================================================


-- ================================================================
-- EXTENSIONS
-- ================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";


-- ================================================================
-- ENUMS
-- ================================================================

CREATE TYPE expense_category AS ENUM (
  'rent',
  'electricity',
  'groceries',
  'utilities',
  'other'
);

CREATE TYPE split_type AS ENUM (
  'equal',
  'custom',
  'percentage'
);

CREATE TYPE payment_status AS ENUM (
  'pending',
  'settled'
);

CREATE TYPE member_role AS ENUM (
  'admin',
  'member'
);


-- ================================================================
-- PROFILES
-- Extension of Supabase Auth users table.
-- id = auth.users.id — set automatically via trigger below.
-- Do not insert directly; Supabase Auth manages the auth.users row.
-- ================================================================

CREATE TABLE profiles (
  id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  name        TEXT NOT NULL,
  email       TEXT NOT NULL,
  upi_id      TEXT,
  phone       TEXT,
  avatar_key  TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Auto-update updated_at on every change
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

CREATE TRIGGER profiles_updated_at
  BEFORE UPDATE ON profiles
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();

-- Auto-create profile row when a new Supabase Auth user signs up
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
  INSERT INTO profiles (id, name, email)
  VALUES (
    NEW.id,
    COALESCE(NEW.raw_user_meta_data->>'full_name', split_part(NEW.email, '@', 1)),
    NEW.email
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION handle_new_user();


-- ================================================================
-- ROOMS
-- ================================================================

CREATE TABLE rooms (
  id          SERIAL PRIMARY KEY,
  name        TEXT NOT NULL,
  address     TEXT,
  room_code   TEXT UNIQUE NOT NULL,
  created_by  UUID NOT NULL REFERENCES profiles(id),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);


-- ================================================================
-- ROOM MEMBERS
-- ================================================================

CREATE TABLE room_members (
  id          SERIAL PRIMARY KEY,
  room_id     INT NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
  user_id     UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  role        member_role NOT NULL DEFAULT 'member',
  joined_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(room_id, user_id)
);


-- ================================================================
-- EXPENSES
-- ================================================================

CREATE TABLE expenses (
  id          SERIAL PRIMARY KEY,
  room_id     INT NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
  title       TEXT NOT NULL,
  amount      NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
  category    expense_category NOT NULL DEFAULT 'other',
  paid_by     UUID NOT NULL REFERENCES profiles(id),
  split_type  split_type NOT NULL DEFAULT 'equal',
  notes       TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);


-- ================================================================
-- EXPENSE SPLITS
-- One row per person per expense representing their share.
-- ================================================================

CREATE TABLE expense_splits (
  id          SERIAL PRIMARY KEY,
  expense_id  INT NOT NULL REFERENCES expenses(id) ON DELETE CASCADE,
  user_id     UUID NOT NULL REFERENCES profiles(id),
  amount      NUMERIC(12, 2) NOT NULL CHECK (amount >= 0),
  is_settled  BOOLEAN NOT NULL DEFAULT false,
  settled_at  TIMESTAMPTZ,
  UNIQUE(expense_id, user_id)
);


-- ================================================================
-- PAYMENTS
-- Direct money transfers between flatmates to settle dues.
-- Two-step: sender records (pending), recipient confirms (settled).
-- ================================================================

CREATE TABLE payments (
  id          SERIAL PRIMARY KEY,
  room_id     INT NOT NULL REFERENCES rooms(id),
  from_user   UUID NOT NULL REFERENCES profiles(id),
  to_user     UUID NOT NULL REFERENCES profiles(id),
  amount      NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
  status      payment_status NOT NULL DEFAULT 'pending',
  upi_ref     TEXT,
  note        TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  settled_at  TIMESTAMPTZ,
  CONSTRAINT no_self_payment CHECK (from_user <> to_user)
);


-- ================================================================
-- INDEXES
-- ================================================================

-- Profiles
CREATE INDEX idx_profiles_email         ON profiles(email);

-- Room members
CREATE INDEX idx_room_members_room      ON room_members(room_id);
CREATE INDEX idx_room_members_user      ON room_members(user_id);

-- Expenses
CREATE INDEX idx_expenses_room          ON expenses(room_id);
CREATE INDEX idx_expenses_paid_by       ON expenses(paid_by);
CREATE INDEX idx_expenses_created_at    ON expenses(created_at DESC);

-- Expense splits
CREATE INDEX idx_splits_expense         ON expense_splits(expense_id);
CREATE INDEX idx_splits_user            ON expense_splits(user_id);
CREATE INDEX idx_splits_unsettled       ON expense_splits(user_id)
  WHERE is_settled = false;

-- Payments
CREATE INDEX idx_payments_room          ON payments(room_id);
CREATE INDEX idx_payments_from          ON payments(from_user);
CREATE INDEX idx_payments_to            ON payments(to_user);
CREATE INDEX idx_payments_status        ON payments(status);
CREATE INDEX idx_payments_created_at    ON payments(created_at DESC);


-- ================================================================
-- ROW LEVEL SECURITY (RLS)
-- The backend uses the service_role key which bypasses RLS.
-- These policies protect any direct client-side Supabase access.
-- ================================================================

ALTER TABLE profiles       ENABLE ROW LEVEL SECURITY;
ALTER TABLE rooms          ENABLE ROW LEVEL SECURITY;
ALTER TABLE room_members   ENABLE ROW LEVEL SECURITY;
ALTER TABLE expenses       ENABLE ROW LEVEL SECURITY;
ALTER TABLE expense_splits ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments       ENABLE ROW LEVEL SECURITY;

-- Profiles: anyone authenticated can read any profile
CREATE POLICY "profiles_select_all"
  ON profiles FOR SELECT
  TO authenticated
  USING (true);

-- Users can only update their own profile
CREATE POLICY "profiles_update_own"
  ON profiles FOR UPDATE
  TO authenticated
  USING (auth.uid() = id);

-- Rooms: only members can see
CREATE POLICY "rooms_select_members_only"
  ON rooms FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM room_members
      WHERE room_id = rooms.id
        AND user_id = auth.uid()
    )
  );

-- Room members: only members of the room can see
CREATE POLICY "room_members_select_members_only"
  ON room_members FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM room_members rm
      WHERE rm.room_id = room_members.room_id
        AND rm.user_id = auth.uid()
    )
  );

-- Expenses: only room members can see
CREATE POLICY "expenses_select_room_members"
  ON expenses FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM room_members
      WHERE room_id = expenses.room_id
        AND user_id = auth.uid()
    )
  );

-- Expense splits: only room members can see
CREATE POLICY "expense_splits_select_room_members"
  ON expense_splits FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM expenses e
      JOIN room_members rm ON rm.room_id = e.room_id
      WHERE e.id = expense_splits.expense_id
        AND rm.user_id = auth.uid()
    )
  );

-- Payments: involved users or room members can see
CREATE POLICY "payments_select_involved"
  ON payments FOR SELECT
  TO authenticated
  USING (
    auth.uid() = from_user
    OR auth.uid() = to_user
    OR EXISTS (
      SELECT 1 FROM room_members
      WHERE room_id = payments.room_id
        AND user_id = auth.uid()
    )
  );


-- ================================================================
-- STORAGE BUCKETS
-- Run these after enabling Storage in your Supabase project.
-- Or create them manually in Dashboard → Storage.
-- ================================================================

INSERT INTO storage.buckets (id, name, public)
VALUES ('avatars', 'avatars', true)
ON CONFLICT (id) DO NOTHING;

INSERT INTO storage.buckets (id, name, public)
VALUES ('receipts', 'receipts', false)
ON CONFLICT (id) DO NOTHING;


-- ================================================================
-- STORAGE POLICIES
-- ================================================================

-- Avatars are public — anyone can view profile pictures
CREATE POLICY "avatars_public_read"
  ON storage.objects FOR SELECT
  USING (bucket_id = 'avatars');

-- Only the authenticated owner can upload their avatar
CREATE POLICY "avatars_owner_write"
  ON storage.objects FOR INSERT
  TO authenticated
  WITH CHECK (
    bucket_id = 'avatars'
    AND auth.uid()::text = (storage.foldername(name))[1]
  );

-- Only the authenticated owner can update/delete their avatar
CREATE POLICY "avatars_owner_update"
  ON storage.objects FOR UPDATE
  TO authenticated
  USING (
    bucket_id = 'avatars'
    AND auth.uid()::text = (storage.foldername(name))[1]
  );

-- Receipts: authenticated users who are room members can read
CREATE POLICY "receipts_authenticated_read"
  ON storage.objects FOR SELECT
  TO authenticated
  USING (bucket_id = 'receipts');

-- Authenticated users can upload receipts
CREATE POLICY "receipts_authenticated_write"
  ON storage.objects FOR INSERT
  TO authenticated
  WITH CHECK (bucket_id = 'receipts');
