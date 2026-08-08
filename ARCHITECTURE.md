# Flatmate — Folder Architecture

This document maps the layout of the Flatmate monorepo. It covers **where things live**, not how to run them — see `README.md` for setup and usage.

```
Flatmate/
├── android/          # Build outputs (signed APK/AAB) + signing keystore
├── backend/          # Python microservices (deployed as AWS Lambdas)
├── frontend/         # React + Capacitor app (web, Android, iOS)
├── scripts/          # Build & deploy automation
├── supabase/         # Database schema for Supabase
├── docker-compose.yml
└── README.md
```

---

## `android/` — Android build artifacts

Not a source tree. Holds the results of the build script and the release key.

| File | Purpose |
|---|---|
| `flatmate-android.apk` | Latest release APK (signed) |
| `flatmate-playstore.aab` | Play Store bundle |
| `flatmate-release.keystore` | Signing key for the release builds — **do not lose or commit** |

---

## `backend/` — Python microservices

Four independent FastAPI services sharing a common `shared/` layer. Each service is packaged and deployed as its own AWS Lambda.

```
backend/
├── shared/                   # Code copied into every Lambda package
│   ├── auth.py               # JWT verification (Supabase tokens)
│   ├── cache.py              # Redis helpers (fault-tolerant)
│   ├── config.py             # Environment/config loading
│   ├── database.py           # PostgreSQL connection
│   ├── s3_utils.py           # S3 file helpers (avatars, etc.)
│   └── supabase_client.py    # Supabase service-role client
│
├── services/
│   ├── user-service/         # Profiles, avatars, UPI
│   ├── room-service/         # Flats, invite codes, members
│   ├── expense-service/      # Expenses, splits, balances, suggestions
│   └── payment-service/      # Payments, settlement confirmation
│
├── database/
│   └── schema.sql            # Postgres schema (source of truth)
│
├── tests/                    # pytest suites (phase1–phase4)
└── requirements.txt
```

Each service follows the same layout:

```
services/<name>-service/
├── Dockerfile               # Local dev container
├── Dockerfile.lambda        # Lambda packaging
├── requirements.txt
├── .env                     # Service-local config
└── src/
    ├── main.py              # FastAPI app entrypoint
    ├── router.py            # HTTP routes
    ├── service.py           # Business logic
    ├── models.py            # DB/ORM models
    ├── schemas.py           # Pydantic request/response schemas
    └── ...                  # Service-specific modules
```

> **Note on imports:** `shared/` modules are copied to the root of each Lambda
> package at build time, so all shared imports are flat — `from config import
> settings`, never `from shared.config import settings`.

---

## `frontend/` — React + Capacitor app

The same codebase serves the web app, the Android app, and (potentially) iOS.
The Android app is a Capacitor shell that wraps the built web app.

```
frontend/
├── public/                   # Static web assets served as-is
│   ├── download.html         # APK download page
│   └── .well-known/
│       └── assetlinks.json   # Android App Links verification
│
├── src/
│   ├── api/                  # Per-domain API clients
│   │   ├── client.ts         # Base HTTP client
│   │   ├── expenseApi.ts
│   │   ├── paymentApi.ts
│   │   ├── roomApi.ts
│   │   └── userApi.ts
│   │
│   ├── components/
│   │   ├── common/           # Shared UI (Button, Modal, Sidebar, Toast, …)
│   │   ├── expenses/         # Expense-specific components
│   │   ├── payments/         # Payment-specific components
│   │   └── room/             # Room/member components
│   │
│   ├── hooks/                # React hooks (useAuth, useExpenses, useRoom, useTheme)
│   │
│   ├── lib/                  # Non-UI helpers
│   │   ├── supabase.ts       # Supabase client
│   │   ├── authFlow.ts       # Login/session finalization
│   │   └── native.ts         # Capacitor native bridges (Google sign-in)
│   │
│   ├── pages/                # Route-level screens
│   │   ├── Login.tsx
│   │   ├── Callback.tsx      # OAuth return handler
│   │   ├── Dashboard.tsx
│   │   ├── Expenses.tsx
│   │   ├── Payments.tsx
│   │   ├── Profile.tsx
│   │   └── Room.tsx
│   │
│   ├── store/                # Zustand stores (auth, expense, room)
│   ├── types/                # Shared TypeScript types (expense, payment, room, user)
│   ├── utils/                # Formatting & pure helpers
│   ├── App.tsx               # Root component + routing
│   ├── App.css               # Global styles & design tokens
│   └── main.tsx              # Entry point
│
├── android/                  # Generated Capacitor Android project (source)
│   └── app/src/main/
│       ├── java/com/flatmate/app/MainActivity.java
│       ├── assets/public/    # Built web app copied here by `cap sync`
│       └── res/              # Android resources (icons, splash)
│
├── capacitor.config.ts       # Capacitor config (appId, plugins)
├── index.html
├── package.json
├── .env                      # Local dev env vars
└── .env.production           # Production env vars (baked into builds)
```

**Key flows:**

- `src/main.tsx` → `src/App.tsx` mounts routing; pages render a shared
  `fm-topbar` header and `src/components/common/Sidebar` / `MobileNav`.
- Auth lives in `src/store/authStore.ts` (Zustand) and `src/lib/authFlow.ts`;
  Google sign-in is bridged through `src/lib/native.ts` using the
  `@capawesome/capacitor-google-sign-in` plugin on Android.
- Env vars are baked in at build time via Vite (`import.meta.env.VITE_*`).

---

## `scripts/` — Build & deploy

| File | Purpose |
|---|---|
| `build-android.sh` | Builds the web app, runs `cap sync`, compiles the signed APK, uploads to S3, invalidates CloudFront |

---

## `supabase/` — Database

| File | Purpose |
|---|---|
| `schema.sql` | Full Supabase schema — enums, tables, RLS policies. Run in the Supabase SQL Editor |

Note: `backend/database/schema.sql` is the Postgres-native copy; `supabase/schema.sql` is the Supabase-managed variant. When schema changes, keep both in sync.
