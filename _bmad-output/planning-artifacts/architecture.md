---
stepsCompleted: ['step-01-init', 'step-02-context', 'step-03-starter', 'step-04-decisions', 'step-05-patterns', 'step-06-structure', 'step-07-validation', 'step-08-complete']
lastStep: 8
status: 'complete'
completedAt: '2026-04-17'
inputDocuments: ['_bmad-output/planning-artifacts/prd.md']
workflowType: 'architecture'
project_name: 'capra-investing-framework'
user_name: 'Karthikmg'
date: '2026-04-17'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**

40 FRs across 7 capability groups:
- Authentication & Access Control (FR1–FR5): JWT login, 24h expiry, server-side invalidation, role detection (Admin/Viewer), protected routes
- Portfolio Management (FR6–FR8): Kite Connect holdings + live quotes, signal badges, navigation to stock analysis
- Stock Search & Analysis (FR9–FR17): Nifty 50 search, 3-pillar hero (Score/Signal/Position Size), expandable detail panels, computation timestamps + data freshness indicators
- Data Refresh & Computation (FR18–FR27): Admin-only triggered refresh, 6 computations (Weighted Score, ROC, Asymmetry Index, Decision Signal, Position Size, Relative Strength), computation audit trail with data version tracking
- Data Ingestion & Upload (FR28–FR34): Screener.in CSV + RBI macro CSV, real-time column schema validation, memory-only pre-validation, atomic replacement, descriptive errors, Admin-only
- User Management (FR35–FR37): Admin CRUD for user accounts with role assignment (Admin/Viewer)
- Security & Data Integrity (FR38–FR40): Encrypted API credentials at rest, HTTPS enforcement, memory-only CSV validation

**Non-Functional Requirements:**

15 NFRs across 3 categories:
- Performance (NFR1–NFR5): Portfolio load <2s, full refresh <3s, CSV validation feedback <500ms, cached stock analysis <1s, React bundle <200KB gzipped
- Security (NFR6–NFR12): TLS 1.2+, AES-256 credential encryption, 24h JWT expiry + server-side invalidation, role enforcement on every request, memory-only CSV validation, no secrets in source control, bcrypt cost 12
- Integration (NFR13–NFR15): Official kiteconnect Python library, Kite response schema validation before computation, computation engine decoupled from Kite client

**Scale & Complexity:**

- Primary domain: Full-stack web application with financial computation engine and multi-source data pipeline
- Complexity level: High
- Estimated architectural components: Auth service, computation engine, dual data pipeline (Kite + CSV), score cache (PostgreSQL), React SPA, FastAPI REST layer, admin management

### Technical Constraints & Dependencies

- **Kite Connect API**: Official Python library only; personal analysis use permitted; no data redistribution. API credentials must be encrypted at rest. Response schema must be validated before entering computation layer.
- **Data localisation**: All user and market data on India-hosted infrastructure (DigitalOcean Mumbai region).
- **Single VPS**: FastAPI serves API + React build from one process. No microservices, no CDN for MVP.
- **Framework is hardcoded**: No user-configurable weights or thresholds in MVP. Computation logic is fixed implementation.
- **Monthly cadence with on-demand refresh**: No real-time streaming, no background polling. User-triggered refresh only.
- **50-stock scope**: Nifty 50 only for MVP. Batch computation must handle 50 stocks × 6 computations within 3-second performance envelope.

### Cross-Cutting Concerns Identified

- **Authentication & RBAC**: JWT validation + role enforcement on every API endpoint; React router enforces protected routes client-side
- **Data audit trail**: Every score computation must store provenance (Kite snapshot timestamp + CSV upload dates per type)
- **Error handling**: Kite API failures (network, auth, schema mismatch), CSV validation failures (column mismatch, corrupt data), computation errors — all must surface to user, none silent
- **Data integrity**: Atomic CSV replacement (all-or-nothing per data type), no partial writes, existing data preserved on validation failure
- **Credential security**: AES-256 encryption for Kite API key/access token; bcrypt for user passwords; environment variable injection for all secrets
- **Batch computation performance**: Full Nifty 50 refresh within 3s requires async/parallel execution of computation pipeline
- **Computation correctness**: Engine must be independently testable with mock data; 100% match against reference cases is a launch gate

## Starter Template Evaluation

### Primary Technology Domain

Full-stack web application — React SPA frontend + Python FastAPI backend, confirmed by PRD specification.

### Starter Options Considered

| Option | Pros | Cons |
|--------|------|------|
| Official Full Stack FastAPI Template | Official, maintained, ships with JWT + user management + PostgreSQL + Tailwind already wired | Separate frontend/backend containers by default (minor adaptation for single-process deploy) |
| DIY: `npm create vite@latest` + manual FastAPI | Maximum flexibility | ~2 days of scaffolding work already solved by the template |
| fastapi-react-starter (community) | Lighter-weight | Less battle-tested, no CI/CD or SQLModel |

### Selected Starter: Full Stack FastAPI Template (Official)

**Repository:** github.com/fastapi/full-stack-fastapi-template

**Rationale for Selection:**
The official template solves FR1–FR5 (JWT auth + role detection) and FR35–FR37 (user management) out of the box — roughly 12 functional requirements that would otherwise require manual scaffolding. It matches the PRD-specified stack exactly.

**Initialization Command:**

```bash
git clone https://github.com/fastapi/full-stack-fastapi-template capra-investing-framework
cd capra-investing-framework
# Rename, configure .env, remove unneeded parts
```

**Architectural Decisions Provided by Starter:**

**Language & Runtime:**
- Frontend: React 19 + TypeScript (strict mode)
- Backend: Python 3.12+, FastAPI 0.135.3

**Styling Solution:**
- Tailwind CSS v4.2.0 via `@tailwindcss/vite` plugin (CSS-first configuration, no separate config file)

**Build Tooling:**
- Vite 8.0.8 with Rolldown bundler (10-30x faster builds)
- Docker Compose for local development

**Testing Framework:**
- Frontend: Vitest (included)
- Backend: pytest (included)

**Code Organization:**
- FastAPI layered structure: `api/` (routers) → `services/` (business logic) → `repositories/` (DB access) → `models/` (SQLAlchemy ORM) → `schemas/` (Pydantic)
- Frontend: feature-grouped component structure under `src/`

**Development Experience:**
- Hot reloading (Vite HMR)
- GitHub Actions CI/CD pre-configured
- Environment variable injection via `.env` (secrets never in source)

**Deployment Adaptation Required:**
The template uses separate Docker containers for frontend/backend. For single-process VPS deploy (PRD requirement), add FastAPI `StaticFiles` mount for the Vite build output:
```python
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")
```

**Note:** Project initialization using this starter is the first implementation story. Custom framework components (computation engine, dual data pipeline, CSV validation, Kite Connect integration) are built on top of this foundation.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- Score cache + audit trail schema (shapes entire computation pipeline)
- JWT via httpOnly cookie + CSRF (shapes auth implementation across all endpoints)
- asyncio + thread pool for batch computation (shapes refresh endpoint design)
- TanStack Query for server state (shapes all frontend data fetching)

**Important Decisions (Shape Architecture):**
- Typed CSV storage tables (shapes data ingestion layer)
- PostgreSQL token blacklist for JWT invalidation (shapes logout + auth middleware)
- Manual Kite token entry in Admin settings for MVP (shapes settings screen + credential storage)
- Alembic for migrations (shapes DB evolution workflow)
- Nginx → Gunicorn → Uvicorn workers (shapes production deployment)

**Deferred Decisions (Post-MVP):**
- DigitalOcean Managed Database (Phase 2 — automated backups, failover)
- In-app Kite Connect OAuth flow (Phase 2 — replaces manual token entry)
- Redis-based token blacklist (Phase 2 — only if scale demands it)

---

### Data Architecture

**Score Cache & Audit Trail**
- Decision: Single `score_snapshots` table per stock per refresh
- Schema: `stock_symbol`, `composite_score`, `signal`, `position_size`, `computation_timestamp`, `kite_snapshot_ts`, `screener_csv_ts`, `rbi_csv_ts`, `factor_breakdown` (JSONB — all 9 weighted factors + individual signals)
- Rationale: Flat schema satisfies FR27 (computation provenance) while keeping queries simple; JSONB for factor breakdown avoids premature normalisation
- Affects: Computation engine output, stock analysis screen (FR10–FR16), data freshness indicators (FR17)

**CSV Data Storage**
- Decision: Dedicated typed tables — `screener_data` (one row per stock per upload batch) and `rbi_macro_data` (one row per upload batch)
- Rationale: Fixed known schemas map cleanly to typed columns; enables column-level validation queries; avoids untyped JSONB payloads
- Affects: CSV ingestion pipeline (FR28–FR34), computation engine inputs

**Database Migrations**
- Decision: Alembic (standard for SQLModel/SQLAlchemy)
- Rationale: Auto-generates migration files from model changes; handles schema evolution without manual SQL; standard in FastAPI ecosystem
- Affects: All DB schema changes across the project lifecycle

---

### Authentication & Security

**JWT Token Storage**
- Decision: httpOnly cookie (not localStorage)
- Rationale: Immune to XSS — JS cannot read httpOnly cookies. Chosen for security correctness even in a personal app context.
- Cascading implication: Requires CSRF protection — use Double Submit Cookie pattern (`fastapi-csrf-protect`)
- Affects: Login endpoint (FR1), all protected API endpoints, React Axios config (cookie sent automatically — no manual header attachment)

**JWT Server-Side Invalidation**
- Decision: PostgreSQL token blacklist — store revoked JTI (JWT ID) until token expiry
- Rationale: Satisfies immediate invalidation on logout (FR2, NFR8) without adding Redis; at single-user scale, DB lookup overhead is negligible
- Affects: Logout endpoint, auth middleware (every request checks blacklist); index the JTI column

**Kite Connect Credential Storage**
- Decision: Admin enters API key + access token manually via Settings screen; stored encrypted at rest (AES-256 via Python `cryptography` library); encryption key in environment variable
- Rationale: Kite Connect requires a browser-based OAuth flow for initial token; manual entry is the simplest MVP approach given monthly cadence. Access token refreshed daily by admin as needed.
- Affects: Admin Settings screen, Kite Connect client initialisation, FR38 (encrypted credentials at rest), NFR7

**CORS Configuration**
- Decision: FastAPI CORSMiddleware restricted to the app's own domain; localhost:5173 allowed in development only
- Rationale: SPA is served from same origin as API in production; CORS only needed for local dev

---

### API & Communication Patterns

**API Design**
- Decision: REST with `/api/v1/` prefix; FastAPI OpenAPI docs at `/docs`
- Rationale: Standard REST matches the request-response pattern of all PRD features; no real-time or GraphQL complexity needed

**Batch Computation Concurrency**
- Decision: Two-phase — (1) async Kite Connect data fetch via `asyncio.gather` (I/O-bound), then (2) synchronous batch score computation in `ThreadPoolExecutor` (CPU-bound)
- Rationale: Satisfies NFR2 (3-second full refresh) without Celery/Redis. Async handles concurrent Kite API calls natively; thread pool handles CPU math without blocking the event loop.
- Affects: `/api/v1/refresh` endpoint design, computation engine interface (must be a pure function — no I/O)

**Error Response Shape**
- Decision: Standardised JSON envelope: `{"error": {"code": "VALIDATION_ERROR", "message": "...", "details": {...}}}`
- Rationale: Consistent shape enables frontend to handle all errors uniformly; `code` field enables specific UI messaging (CSV column errors vs auth errors vs Kite failures)
- Affects: All API endpoints, frontend error handling

---

### Frontend Architecture

**Server State Management**
- Decision: TanStack Query v5 (React Query)
- Rationale: Purpose-built for fetch + cache + stale-while-revalidate; eliminates loading/error boilerplate; pairs naturally with user-triggered refresh (manual cache invalidation on refresh button click)
- Affects: All data-fetching components — portfolio view, stock analysis, upload screen

**HTTP Client**
- Decision: Axios — cookie-based auth means no manual JWT header attachment; Axios interceptors handle 401 → redirect to login
- Affects: All API calls from React

**Routing**
- Decision: React Router v7 with protected route wrappers — unauthenticated requests redirect to `/login`; role-based route guards for Admin-only screens (Upload, Settings)
- Affects: App shell, all screen components

---

### Infrastructure & Deployment

**Process Stack**
- Decision: Nginx (SSL termination + reverse proxy) → Gunicorn (process manager) → Uvicorn workers (ASGI)
- Rationale: Production-standard FastAPI deployment; Nginx handles HTTPS (NFR6); FastAPI mounts React build via StaticFiles
- Affects: VPS setup, deployment scripts

**Environment Configuration**
- Decision: `.env` files for local dev; environment variable injection on VPS; `pydantic-settings` (`BaseSettings`) for typed config in FastAPI; no secrets in source control (NFR11)
- Affects: All credential and config references in backend

**PostgreSQL Hosting**
- Decision: Same VPS as application for MVP; manual `pg_dump` cron for interim backups
- Rationale: Simplicity acceptable for personal use at monthly cadence
- Deferred: DigitalOcean Managed DB for Phase 2

---

### Decision Impact Analysis

**Implementation Sequence:**
1. DB schema + Alembic setup (everything depends on it)
2. Auth middleware (httpOnly cookie + CSRF + JTI blacklist) — gates all other endpoints
3. Kite Connect client + credential decrypt → computation engine (core value loop)
4. CSV ingestion + validation pipeline (completes the data pipeline)
5. React Router protected routes + TanStack Query setup (gates all screen work)

**Cross-Component Dependencies:**
- httpOnly cookie → CSRF middleware must be added before any state-mutating endpoints
- JTI blacklist → index the JTI column; every auth check hits DB
- asyncio.gather for Kite fetch → computation engine must be a pure function (no I/O) callable from thread pool
- TanStack Query → refresh button triggers manual cache invalidation, not page reload

## Implementation Patterns & Consistency Rules

### Critical Conflict Points Identified

6 areas where AI agents could diverge without explicit rules:
1. JSON field naming at the Python↔TypeScript boundary (snake_case vs camelCase)
2. API response envelope shape (direct vs wrapped)
3. Frontend component and file naming conventions
4. Test file location and naming
5. Python exception hierarchy and error propagation
6. Auth dependency injection patterns

---

### Naming Patterns

**Database Naming Conventions:**
- Tables: `snake_case`, plural — `users`, `score_snapshots`, `screener_data`, `rbi_macro_data`, `revoked_tokens`
- Columns: `snake_case` — `stock_symbol`, `composite_score`, `created_at`, `kite_snapshot_ts`
- Primary keys: always `id` (UUID preferred for user-facing tables)
- Foreign keys: `{table_singular}_id` — `user_id`, never `fk_user` or `userId`
- Indexes: `ix_{table}_{column}` — `ix_score_snapshots_stock_symbol`, `ix_revoked_tokens_jti`
- Timestamps: always `created_at` and `updated_at` (never `createdAt`, `timestamp`, `date`)

**API Naming Conventions:**
- Endpoints: `snake_case`, plural resources — `/api/v1/stocks`, `/api/v1/score_snapshots`, `/api/v1/users`
- Path parameters: `snake_case` — `/api/v1/stocks/{stock_symbol}` (not `{stockSymbol}`)
- Query parameters: `snake_case` — `?stock_symbol=HDFCBANK`
- HTTP verbs: GET (read), POST (create), PUT (full replace), PATCH (partial update), DELETE

**JSON Field Naming — Critical Rule:**
- **All JSON fields use `snake_case`** throughout — API responses, request bodies, TypeScript types
- Rationale: FastAPI/Pydantic defaults to snake_case; avoids a conversion layer at the Python/TypeScript boundary
- Example: `{"stock_symbol": "HDFCBANK", "composite_score": 0.61, "kite_snapshot_ts": "2026-04-17T10:00:00Z"}`
- Anti-pattern: `{"stockSymbol": "HDFCBANK", "compositeScore": 0.61}` — never

**Python Code Naming:**
- Files: `snake_case` — `stock_service.py`, `computation_engine.py`, `kite_client.py`
- Classes: `PascalCase` — `StockService`, `ComputationEngine`, `ScoreSnapshot`
- Functions/methods: `snake_case` — `compute_weighted_score()`, `get_holdings()`
- Constants: `UPPER_SNAKE_CASE` — `NIFTY_50_SYMBOLS`, `JWT_ALGORITHM`
- Variables: `snake_case` — `stock_symbol`, `composite_score`

**TypeScript/React Code Naming:**
- Component files: `PascalCase.tsx` — `StockCard.tsx`, `PortfolioView.tsx`, `ScorePillar.tsx`
- Non-component files: `camelCase.ts` — `apiClient.ts`, `useStockScore.ts`, `formatters.ts`
- React components: `PascalCase` — `function StockCard()`
- Hooks: `use` prefix — `useStockScore`, `usePortfolio`, `useRefresh`
- TypeScript types/interfaces: `PascalCase` — `ScoreSnapshot`, `StockSignal`, `UserRole`
- Variables: `camelCase` — `stockSymbol`, `compositeScore`, `isLoading`

---

### Structure Patterns

**Backend Project Organization (`backend/app/`):**
```
api/v1/
  auth.py          # /api/v1/auth/* routes
  stocks.py        # /api/v1/stocks/* routes
  portfolio.py     # /api/v1/portfolio/* routes
  upload.py        # /api/v1/upload/* routes
  users.py         # /api/v1/users/* routes
  refresh.py       # /api/v1/refresh route
  dependencies.py  # Shared FastAPI Depends() — get_current_user, require_admin
core/
  config.py        # pydantic-settings BaseSettings
  security.py      # JWT encode/decode, CSRF, bcrypt
  encryption.py    # AES-256 encrypt/decrypt for Kite credentials
services/
  computation_engine.py  # Pure functions — no I/O, all 6 computations
  kite_client.py         # Kite Connect API wrapper
  csv_validator.py       # Column schema validation, memory-only
  score_service.py       # Orchestrates fetch + compute + save
models/             # SQLModel ORM models (DB tables)
schemas/            # Pydantic schemas (API request/response shapes)
tests/              # All backend tests here
  test_computation_engine.py
  test_csv_validator.py
  test_api_auth.py
```

**Frontend Project Organization (`frontend/src/`):**
```
features/
  auth/
    LoginPage.tsx
    useAuth.ts
  portfolio/
    PortfolioView.tsx
    PortfolioRow.tsx
    usePortfolio.ts
  stock/
    StockAnalysis.tsx
    ScorePillar.tsx
    SignalPillar.tsx
    PositionPillar.tsx
    useStockScore.ts
  upload/
    UploadScreen.tsx
    useUpload.ts
  admin/
    AdminSettings.tsx
    UserManagement.tsx
shared/
  components/       # Truly shared UI primitives only
  hooks/            # Shared hooks (useRefresh, useCurrentUser)
  types/            # All TypeScript type definitions
  lib/
    apiClient.ts    # Axios instance with interceptors
    queryClient.ts  # TanStack Query client setup
```

**Test File Location:**
- Backend: `backend/app/tests/test_{module}.py` — never co-located with source
- Frontend: Co-located `{ComponentName}.test.tsx` alongside the component file

---

### Format Patterns

**API Response Formats:**

Success (single resource):
```json
{"id": 1, "stock_symbol": "HDFCBANK", "composite_score": 0.61}
```

Success (collection):
```json
{"items": [...], "total": 50}
```

Success (action with no body):
```json
{"status": "ok"}
```

Error (all failures):
```json
{"error": {"code": "CSV_COLUMN_MISSING", "message": "Column 'PE_Ratio' not found.", "details": {"expected": ["PE_Ratio", "PB_Ratio"], "found": ["pe_ratio"]}}}
```

HTTP status codes:
- 200: successful read
- 201: successful creation
- 204: successful deletion (empty body)
- 400: validation error (bad input)
- 401: unauthenticated
- 403: authenticated but insufficient role
- 422: Pydantic validation failure (FastAPI default)
- 500: unhandled server error

**Date/Time Format:**
- All timestamps: ISO 8601 UTC strings — `"2026-04-17T10:30:00Z"` (never Unix timestamps, never local time)
- Date-only fields: `"2026-04-17"`

**Numeric Precision:**
- Scores (−1 to +1): 4 decimal places — `0.6125`
- Percentages: 2 decimal places — `65.00`
- Prices: 2 decimal places — `1842.50`

---

### Process Patterns

**Backend Error Propagation:**
- Services raise custom domain exceptions defined in `core/exceptions.py` — e.g., `CSVValidationError`, `KiteAPIError`
- API routers catch domain exceptions and convert to `HTTPException` with the standard error envelope
- Never raise `HTTPException` directly from service layer — services must be testable without HTTP context
- Kite API errors always logged at `ERROR` level and surfaced as `{"error": {"code": "KITE_API_ERROR", ...}}`

**Auth Dependency Injection (FastAPI):**
- `Depends(get_current_user)` → returns current `User` or raises 401 — use on all protected routes
- `Depends(require_admin)` → calls `get_current_user` then checks `role == "admin"`, raises 403 — use on Admin-only routes
- Never inline JWT validation logic in route handlers — always via `Depends`

**Frontend Loading & Error States:**
- Use TanStack Query's `isLoading`, `isError`, `error`, `data` — never maintain local `useState` for server data
- Loading state: show skeleton/spinner component, never disable the whole page
- Error state: show inline error message near the triggering element (not a global modal for non-auth errors)
- 401 response: Axios interceptor redirects to `/login` — no component-level handling needed

**CSV Validation Pattern:**
- Validation is always memory-only — read file into `bytes`, parse in-memory, never `open()` to disk
- Validate columns first (fast, < 500ms), then data types, then business rules
- On any validation failure: return error immediately, make zero DB writes
- On validation success: wrap DB write in a transaction — rollback on any error

**Computation Engine Pattern:**
- All 6 computation functions are pure: `def compute_weighted_score(factors: FactorInputs) -> float`
- No database calls, no Kite calls, no side effects inside computation functions
- `score_service.py` is the only orchestrator: fetch data → call computation functions → persist results
- All computation functions must have unit tests with manually verified reference cases

---

### Enforcement Guidelines

**All AI Agents MUST:**
- Use `snake_case` for all JSON field names — no exceptions
- Raise domain exceptions from services, convert to HTTP responses only at the router layer
- Use `Depends(get_current_user)` or `Depends(require_admin)` on every protected route — never skip
- Keep computation engine functions pure (no I/O)
- Wrap all CSV-triggered DB writes in transactions
- Use TanStack Query for all server state — no `useState` + `useEffect` for API calls

**Anti-Patterns (Never Do):**
- `camelCase` in API JSON fields — breaks the Python/TypeScript boundary
- `HTTPException` raised from service layer — breaks testability
- Inline JWT decode in route handler — bypasses auth middleware
- `open(csv_file, 'r')` for CSV validation — violates NFR10 (memory-only requirement)
- `useState<Data>(null)` + `useEffect(() => fetch(...))` — use TanStack Query instead
- Hardcoded framework weights or thresholds — all constants in `core/config.py` or `core/constants.py`

## Project Structure & Boundaries

### Complete Project Directory Structure

```
capra-investing-framework/
├── docker-compose.yml             # Dev: backend + frontend + postgres
├── docker-compose.prod.yml        # Prod: backend (serves frontend build) + postgres
├── .env.example
├── .gitignore
├── README.md
└── .github/
    └── workflows/
        └── ci.yml                 # Backend tests + frontend build check

backend/
├── app/
│   ├── main.py                    # FastAPI app entry, StaticFiles mount, middleware
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py            # POST /auth/login, POST /auth/logout, GET /auth/me
│   │       ├── stocks.py          # GET /stocks, GET /stocks/{stock_symbol}
│   │       ├── portfolio.py       # GET /portfolio
│   │       ├── upload.py          # POST /upload/screener, POST /upload/rbi
│   │       ├── refresh.py         # POST /refresh (admin only)
│   │       ├── users.py           # GET/POST/PATCH/DELETE /users (admin only)
│   │       ├── settings.py        # GET/PUT /settings/kite (admin only)
│   │       └── dependencies.py    # get_current_user, require_admin
│   ├── core/
│   │   ├── config.py              # pydantic-settings BaseSettings
│   │   ├── security.py            # JWT encode/decode, bcrypt, CSRF
│   │   ├── encryption.py          # AES-256 for Kite credentials
│   │   ├── exceptions.py          # CSVValidationError, KiteAPIError, ComputationError
│   │   └── constants.py           # NIFTY_50_SYMBOLS, factor weights, decision matrix
│   ├── services/
│   │   ├── computation_engine.py  # Pure functions — all 6 computations, no I/O
│   │   ├── kite_client.py         # Kite Connect wrapper (holdings, prices, indices)
│   │   ├── csv_validator.py       # Memory-only column schema + type validation
│   │   └── score_service.py       # Orchestrator: asyncio fetch → thread compute → persist
│   ├── models/                    # SQLModel ORM (maps to DB tables)
│   │   ├── user.py                # users table
│   │   ├── score_snapshot.py      # score_snapshots table (with factor_breakdown JSONB)
│   │   ├── screener_data.py       # screener_data table (per stock per upload batch)
│   │   ├── rbi_macro_data.py      # rbi_macro_data table (per upload batch)
│   │   └── revoked_token.py       # revoked_tokens table (JTI blacklist)
│   ├── schemas/                   # Pydantic (API request/response shapes only)
│   │   ├── auth.py                # LoginRequest, TokenResponse, UserResponse
│   │   ├── stock.py               # StockScoreResponse, FactorBreakdown, SignalDetail
│   │   ├── portfolio.py           # PortfolioResponse, HoldingResponse
│   │   ├── upload.py              # UploadResponse, CSVValidationError
│   │   └── user.py                # UserCreate, UserUpdate, UserResponse
│   ├── database.py                # SQLModel engine, session factory, get_session
│   └── tests/
│       ├── conftest.py            # pytest fixtures: test DB, mock kite client, auth cookies
│       ├── test_computation_engine.py  # Pure function tests + reference case assertions
│       ├── test_csv_validator.py  # Valid/invalid CSV scenarios
│       ├── test_api_auth.py       # Login, logout, token expiry, role enforcement
│       ├── test_api_stocks.py     # Score retrieval, freshness indicators
│       ├── test_api_upload.py     # Column validation, atomic write, error messages
│       └── test_api_refresh.py    # Refresh trigger, computation correctness, audit trail
├── alembic/
│   ├── alembic.ini
│   ├── env.py
│   └── versions/                  # Generated migration files
├── requirements.txt
├── requirements-dev.txt
└── Dockerfile

frontend/
├── index.html
├── vite.config.ts                 # @tailwindcss/vite plugin
├── tsconfig.json
├── tsconfig.node.json
├── package.json
├── .env
├── .env.example
├── src/
│   ├── main.tsx                   # React app entry
│   ├── App.tsx                    # React Router setup, protected route wrappers
│   ├── index.css                  # @import "tailwindcss"
│   ├── features/
│   │   ├── auth/
│   │   │   ├── LoginPage.tsx      # FR1 — email/password login form
│   │   │   ├── LoginPage.test.tsx
│   │   │   └── useAuth.ts         # Auth state, login/logout mutations
│   │   ├── portfolio/
│   │   │   ├── PortfolioView.tsx  # FR6–FR8 — holdings list, signal badges, refresh button
│   │   │   ├── PortfolioRow.tsx   # Single holding row with live quote + signal badge
│   │   │   ├── SignalBadge.tsx    # 5-state signal visual (green/yellow/white/orange/red)
│   │   │   ├── PortfolioView.test.tsx
│   │   │   └── usePortfolio.ts    # TanStack Query → GET /portfolio
│   │   ├── stock/
│   │   │   ├── StockAnalysis.tsx  # FR9–FR17 — search + 3-pillar hero layout
│   │   │   ├── StockSearch.tsx    # FR9 — Nifty 50 typeahead search
│   │   │   ├── ScorePillar.tsx    # FR10, FR13 — composite score + expandable factor breakdown
│   │   │   ├── SignalPillar.tsx   # FR11, FR14 — signal + ROC, Asymmetry, Time Stop
│   │   │   ├── PositionPillar.tsx # FR12, FR15 — position size + step-by-step calculation
│   │   │   ├── DataFreshness.tsx  # FR16, FR17 — computation ts + Kite/CSV staleness
│   │   │   ├── StockAnalysis.test.tsx
│   │   │   └── useStockScore.ts   # TanStack Query → GET /stocks/{stock_symbol}
│   │   ├── upload/
│   │   │   ├── UploadScreen.tsx   # FR28–FR34 — dual CSV upload + validation feedback
│   │   │   ├── FileDropZone.tsx   # File input with drag-and-drop
│   │   │   ├── ValidationResult.tsx # Column-level error display
│   │   │   ├── UploadScreen.test.tsx
│   │   │   └── useUpload.ts       # TanStack mutation → POST /upload/screener, /upload/rbi
│   │   └── admin/
│   │       ├── AdminSettings.tsx  # FR38 — Kite API key + access token entry
│   │       ├── UserManagement.tsx # FR35–FR37 — user list, create, deactivate
│   │       ├── UserForm.tsx       # Create/edit user form (role selector)
│   │       └── useUsers.ts        # TanStack Query → GET/POST/PATCH/DELETE /users
│   ├── shared/
│   │   ├── components/
│   │   │   ├── ProtectedRoute.tsx # FR3 — redirect unauthenticated to /login
│   │   │   ├── AdminRoute.tsx     # FR4 — redirect non-admin (403 guard)
│   │   │   ├── LoadingSpinner.tsx
│   │   │   └── ErrorMessage.tsx
│   │   ├── hooks/
│   │   │   ├── useRefresh.ts      # FR18/FR19 — trigger refresh, invalidate all queries
│   │   │   └── useCurrentUser.ts  # Current user + role from /auth/me
│   │   ├── types/
│   │   │   ├── stock.ts           # ScoreSnapshot, StockSignal, FactorBreakdown
│   │   │   ├── portfolio.ts       # HoldingResponse, PortfolioResponse
│   │   │   ├── user.ts            # User, UserRole ("admin" | "viewer")
│   │   │   └── api.ts             # ApiError, ApiCollection<T>
│   │   └── lib/
│   │       ├── apiClient.ts       # Axios instance: withCredentials, 401 → /login
│   │       └── queryClient.ts     # TanStack Query client: staleTime, retry config
├── public/
└── dist/                          # Vite build output (mounted by FastAPI StaticFiles)
```

---

### Architectural Boundaries

**API Boundaries:**

| Boundary | Rule |
|----------|------|
| Public | `POST /api/v1/auth/login` only — no JWT required |
| Authenticated | All other `/api/v1/*` — valid httpOnly JWT cookie required |
| Admin-only | `/api/v1/refresh`, `/api/v1/upload/*`, `/api/v1/users`, `/api/v1/settings/kite` — role == "admin" |
| Static SPA | `GET /` and all non-`/api/` paths — served from `frontend/dist/` via StaticFiles |

**Service Boundaries:**
- `computation_engine.py` — pure functions only; no imports from `kite_client`, `database`, or any I/O module
- `kite_client.py` — all Kite Connect I/O; decrypts credentials on init; validates response schema before returning
- `csv_validator.py` — all validation logic; accepts `bytes` input; returns `ValidationResult`, never touches DB
- `score_service.py` — the only module that calls both `kite_client` AND `computation_engine` AND DB; sole owner of the refresh transaction

**Data Boundaries:**
- `screener_data` and `rbi_macro_data` tables are append-on-upload with `upload_batch_id`; computation always reads the latest batch
- `score_snapshots` table is append-on-refresh; UI always reads the latest snapshot per stock
- `revoked_tokens` table is write-on-logout, read-on-every-auth-check; JTI column indexed

---

### Requirements to Structure Mapping

| FR Group | Backend | Frontend |
|----------|---------|----------|
| FR1–FR5 (Auth) | `api/v1/auth.py`, `core/security.py`, `models/revoked_token.py` | `features/auth/`, `shared/components/ProtectedRoute.tsx` |
| FR6–FR8 (Portfolio) | `api/v1/portfolio.py`, `services/kite_client.py` | `features/portfolio/` |
| FR9–FR17 (Stock Analysis) | `api/v1/stocks.py`, `models/score_snapshot.py` | `features/stock/` |
| FR18–FR27 (Refresh + Computation) | `api/v1/refresh.py`, `services/score_service.py`, `services/computation_engine.py`, `core/constants.py` | `shared/hooks/useRefresh.ts` |
| FR28–FR34 (CSV Upload) | `api/v1/upload.py`, `services/csv_validator.py`, `models/screener_data.py`, `models/rbi_macro_data.py` | `features/upload/` |
| FR35–FR37 (User Management) | `api/v1/users.py`, `models/user.py` | `features/admin/UserManagement.tsx` |
| FR38–FR40 (Security) | `core/encryption.py`, `api/v1/settings.py` | `features/admin/AdminSettings.tsx` |

---

### Data Flow

**Refresh cycle (core value loop):**
```
POST /api/v1/refresh (admin only)
  → score_service.py
    → asyncio.gather: kite_client.get_prices(), get_holdings(), get_indices()  [I/O phase]
    → ThreadPoolExecutor: computation_engine.compute_*() × 50 stocks           [CPU phase]
    → DB transaction: INSERT INTO score_snapshots (one row per stock)
  → {"status": "ok"}
  → Frontend: useRefresh() invalidates all TanStack Query caches
```

**CSV upload (data ingestion loop):**
```
POST /api/v1/upload/screener (multipart, admin only)
  → csv_validator.validate_screener(file_bytes)  [memory-only, < 500ms]
    → if invalid: return {"error": {"code": "CSV_COLUMN_MISSING", ...}}  [zero DB writes]
    → if valid: DB transaction: INSERT INTO screener_data (batch)
  → {"status": "ok"}
```

**Stock analysis (read path):**
```
GET /api/v1/stocks/{stock_symbol}
  → SELECT * FROM score_snapshots WHERE stock_symbol = ? ORDER BY computation_timestamp DESC LIMIT 1
  → StockScoreResponse (includes factor_breakdown JSONB + all freshness timestamps)
```

---

### Development Workflow

**Local dev:**
```bash
docker-compose up          # Starts postgres + backend (uvicorn --reload) + frontend (vite dev)
```

**Backend tests:**
```bash
cd backend && pytest app/tests/ -v
```

**Frontend build check:**
```bash
cd frontend && npm run build   # Vite build → dist/; FastAPI StaticFiles picks this up
```

**Production deploy (single VPS):**
```bash
# Build frontend
cd frontend && npm run build

# Start backend (serves frontend/dist via StaticFiles)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Nginx proxies 443 → gunicorn:8000
```

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
- FastAPI 0.135.3 + SQLModel + Alembic are compatible and actively co-maintained
- React 19 + Vite 8 + Tailwind v4 + TanStack Query v5 are all 2026-current and compatible
- httpOnly JWT cookie + Axios `withCredentials: true` + CSRF Double Submit pattern are compatible
- asyncio.gather (I/O phase) + ThreadPoolExecutor (CPU phase) is a valid FastAPI async pattern
- AES-256 via Python `cryptography` library + env var encryption key is compatible with pydantic-settings

**Pattern Consistency:**
All naming conventions, structure patterns, and process patterns are internally consistent and aligned with chosen stack defaults. No contradictions found.

**Structure Alignment:**
Project structure directly maps each FR group to specific files. Service layer boundaries enforce the computation engine's pure-function requirement. All integration points are explicitly defined.

---

### Requirements Coverage Validation ✅

**Functional Requirements (40/40 covered):**

| FR Group | Status | Notes |
|----------|--------|-------|
| FR1–FR5 Auth | ✅ | httpOnly JWT cookie, JTI blacklist, role enforcement |
| FR6–FR8 Portfolio | ✅ | kite_client → portfolio endpoint → PortfolioView |
| FR9–FR17 Stock Analysis | ✅ | score_snapshots + factor_breakdown JSONB (schema defined below) |
| FR18–FR27 Refresh/Computation | ✅ | asyncio + ThreadPoolExecutor, 6 pure functions, audit trail |
| FR28–FR34 CSV Upload | ✅ | memory-only validation, atomic replacement, descriptive errors |
| FR35–FR37 User Management | ✅ | CRUD /users admin-only endpoints |
| FR38–FR40 Security | ✅ | AES-256, Nginx HTTPS, bytes-only CSV |

**Non-Functional Requirements (15/15 covered):**

| NFR | Status | Architectural Support |
|-----|--------|-----------------------|
| NFR1 (portfolio < 2s) | ✅ | Async Kite call + cached scores |
| NFR2 (refresh < 3s) | ✅ | asyncio.gather + ThreadPoolExecutor batch |
| NFR3 (CSV validation < 500ms) | ✅ | Memory-only, column check first |
| NFR4 (cached analysis < 1s) | ✅ | Single SELECT from score_snapshots |
| NFR5 (bundle < 200KB gzipped) | ✅ | Vite Rolldown + Tailwind purge + route code splitting |
| NFR6–NFR12 (Security) | ✅ | Nginx TLS, AES-256, bcrypt 12, JTI blacklist, env vars |
| NFR13–NFR15 (Integration) | ✅ | kiteconnect library, response schema validation, pure engine |

---

### Gap Analysis & Resolutions

**Gap 1 — factor_breakdown JSONB Schema (Important)**

FR14 and FR15 require storing computed intermediates beyond the 9 weighted factors. The JSONB must include:

```json
{
  "factors": [
    {
      "name": "relative_strength",
      "weight": 0.15,
      "raw_value": 0.72,
      "weighted_contribution": 0.108,
      "signal": "positive"
    }
  ],
  "roc": 0.087,
  "asymmetry_index": 0.42,
  "time_stop_months": 3,
  "position_breakdown": {
    "base_pct": 65.0,
    "conviction_multiplier": 1.5,
    "volatility_adjustment": 0.9,
    "final_pct": 87.75
  }
}
```

All 9 factors must be present in the `factors` array. The `computation_engine.py` output schema must exactly match this structure.

**Gap 2 — StaticFiles Mount Order (Important)**

In `backend/app/main.py`, API routes MUST be registered before the StaticFiles mount. Reversing this order silently routes all API calls to the SPA — a hard-to-diagnose bug.

```python
# CORRECT order in main.py
app.include_router(api_v1_router, prefix="/api/v1")   # FIRST — all API routes
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")  # LAST
```

**Gap 3 — Cookie Configuration Per Environment (Minor)**

JWT httpOnly cookie settings must differ between environments:

| Setting | Development | Production |
|---------|-------------|------------|
| `HttpOnly` | True | True |
| `Secure` | False (HTTP localhost) | True (HTTPS only) |
| `SameSite` | Lax | Strict |

Axios `apiClient.ts` must set `withCredentials: true` globally — otherwise cookies are not sent with API requests.

**Gap 4 — revoked_tokens Cleanup (Minor)**

On each successful login, delete rows from `revoked_tokens` where `expires_at < NOW()`. Prevents unbounded table growth at negligible cost (indexed query at login time).

---

### Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] 40 FRs analyzed and architecturally mapped
- [x] 15 NFRs addressed with specific technical decisions
- [x] Technical constraints identified (Kite Connect ToS, data localisation, single VPS)
- [x] Cross-cutting concerns mapped (auth, audit trail, error handling, data integrity)

**✅ Architectural Decisions**
- [x] Critical decisions documented with verified versions
- [x] Full technology stack specified (FastAPI 0.135.3, React 19, Vite 8, Tailwind v4, TanStack Query v5)
- [x] Security architecture defined (httpOnly cookie, JTI blacklist, AES-256, CSRF)
- [x] Performance architecture defined (asyncio + ThreadPoolExecutor, score cache)

**✅ Implementation Patterns**
- [x] Naming conventions: DB, API, JSON, Python, TypeScript
- [x] Structure patterns: backend layering, feature-grouped frontend
- [x] Error handling: domain exceptions → HTTP conversion at router layer
- [x] Auth: Depends() injection, never inline
- [x] 6 anti-patterns explicitly documented

**✅ Project Structure**
- [x] Complete directory tree with all files named and annotated
- [x] FR-to-file mapping table
- [x] All 3 data flows documented (refresh, upload, read)
- [x] Development + production workflow commands

---

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** High — all 40 FRs mapped to specific files, all 15 NFRs have architectural support, all critical conflict points addressed, gaps resolved.

**Key Strengths:**
- Computation engine isolated as pure functions — independently testable without Kite credentials
- Dual data pipeline (Kite + CSV) with explicit audit trail satisfies both automation and manual upload use cases
- httpOnly cookie + JTI blacklist provides strong auth security appropriate for financial data sensitivity
- factor_breakdown JSONB enables full FR13–FR15 expansion UI without additional DB queries
- asyncio + thread pool achieves 3-second refresh target without adding queue infrastructure

**Areas for Future Enhancement (Post-MVP):**
- Redis token blacklist (Phase 2 — if multi-user scale requires faster lookups)
- DigitalOcean Managed DB (Phase 2 — automated backups and failover)
- In-app Kite OAuth flow (Phase 2 — replaces manual token entry)
- Score history charting (Phase 2 PRD feature)

---

### Implementation Handoff

**First Story:** Initialize from the Full Stack FastAPI Template:
```bash
git clone https://github.com/fastapi/full-stack-fastapi-template capra-investing-framework
```
Then adapt to single-process deployment and configure per this architecture document.

**Implementation Order:**
1. DB schema + Alembic migrations (all models)
2. Auth — httpOnly cookie, CSRF, JTI blacklist, `get_current_user`, `require_admin`
3. Computation engine — pure functions with reference case tests
4. Kite Connect client + score service (refresh cycle)
5. CSV validator + upload endpoints
6. React Router protected routes + TanStack Query + apiClient
7. Feature screens in order: Portfolio → Stock Analysis → Upload → Admin
