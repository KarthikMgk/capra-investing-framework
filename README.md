# Capra Investing Framework

A personal web application that operationalises the **Multi-Layer Capital Allocation System v3.0** — a 15-factor, regime-based framework for entry, exit, and position sizing decisions on Nifty 50 stocks.

The app replaces a manual spreadsheet with an automated cockpit: search a stock, hit refresh, get the answer in under 3 seconds.

---

## The Decision Surface

Every stock analysis produces a single 3-pillar answer:

| Pillar | What it answers |
|---|---|
| **Score** | Weighted composite across 9 factors (−1 to +1) |
| **Signal** | 5-state decision: Strong Buy / Buy / Hold / Sell / Strong Sell |
| **Position Size** | 3-layer sizing: Base × Conviction multiplier × Volatility adjustment |

Each pillar is expandable to show the full factor breakdown, conditions that triggered the signal, and the step-by-step position size calculation.

---

## Tech Stack

**Backend**
- Python 3.12 · FastAPI · SQLModel · PostgreSQL
- Cookie-based JWT auth (httpOnly) with JTI blacklist (server-side logout)
- AES-256 encryption for Kite API credentials at rest
- Argon2 password hashing (via pwdlib)

**Frontend**
- React 19 · TypeScript · Vite
- TanStack Router (file-based routing) · TanStack Query
- Tailwind CSS v4 · shadcn/ui components
- Playwright for E2E tests

**Infrastructure**
- Docker Compose (single VPS deployment)
- Traefik reverse proxy with automatic TLS
- DigitalOcean Mumbai (data localisation for Indian equities)

**Data Sources**
- [Kite Connect API](https://kite.trade) — live prices, portfolio holdings, Nifty 50 index, USD/INR, Gold
- Screener.in CSV — Nifty 50 fundamentals and earnings data (manual upload, monthly cadence)
- RBI macro CSV — repo rate, credit growth, liquidity indicators (manual upload, monthly cadence)

---

## Roles

| Role | Capabilities |
|---|---|
| **Admin** | All access — trigger refresh, upload CSVs, manage users, view analysis |
| **Viewer** | Read-only — view portfolio, stock analysis, signals |

---

## Project Structure

```
capra-investing-framework/
├── backend/                  # FastAPI application
│   ├── app/
│   │   ├── api/routes/       # auth, users, upload, computation, portfolio
│   │   ├── core/             # config, security, exceptions
│   │   ├── models/           # SQLModel DB models
│   │   ├── schemas/          # Pydantic API schemas
│   │   ├── crud/             # Database operations
│   │   └── computation/      # Score engine (decoupled from Kite client)
│   ├── alembic/              # DB migrations
│   └── tests/
├── frontend/                 # React SPA
│   └── src/
│       ├── routes/           # TanStack file-based routes
│       ├── components/       # UI components (shadcn + custom)
│       ├── hooks/            # TanStack Query hooks
│       └── client/           # Auto-generated API client
├── _bmad-output/             # Design artifacts (PRD, architecture, epics)
├── compose.yml               # Development Docker Compose
├── compose.traefik.yml       # Production Traefik config
└── .env.example              # Environment variable reference
```

---

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.12+ (for running backend tests outside Docker)
- Node.js / Bun (for frontend development)

### 1. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

```bash
SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_urlsafe(32))">
ENCRYPTION_KEY=<generate: python -c "import secrets; print(secrets.token_urlsafe(32))">
KITE_ENCRYPTION_KEY=<generate: python -c "import secrets; print(secrets.token_urlsafe(32))">
FIRST_SUPERUSER_PASSWORD=<your admin password>
POSTGRES_PASSWORD=<your db password>
```

### 2. Start the stack

```bash
docker compose up -d
```

Services:
- Backend API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Frontend: `http://localhost:5173` (dev server) or served from backend in production
- Mailcatcher: `http://localhost:1080`

### 3. Default admin credentials

```
Email:    admin@capra.example.com   (set via FIRST_SUPERUSER_EMAIL)
Password: changeme                  (set via FIRST_SUPERUSER_PASSWORD)
```

The admin user is seeded automatically on first startup.

---

## Development

### Backend

```bash
cd backend

# Run tests
python -m pytest

# Run specific test files
python -m pytest tests/test_api_auth.py -v

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "description"
```

### Frontend

```bash
cd frontend

bun install
bun dev          # start dev server on :5173
bunx playwright test         # E2E tests
bunx playwright test --ui    # Playwright UI mode
```

### Regenerate API client (after backend schema changes)

```bash
cd frontend
bun run generate-client
```

---

## Environment Variables

| Variable | Description | Required |
|---|---|---|
| `SECRET_KEY` | JWT signing key (min 32 chars) | Yes |
| `ENCRYPTION_KEY` | General encryption key (32-byte base64) | Yes |
| `KITE_ENCRYPTION_KEY` | Kite credential encryption key (32-byte base64) | Yes |
| `POSTGRES_PASSWORD` | PostgreSQL password | Yes |
| `FIRST_SUPERUSER_EMAIL` | Admin user email (seeded on startup) | Yes |
| `FIRST_SUPERUSER_PASSWORD` | Admin user password | Yes |
| `ENVIRONMENT` | `local` \| `staging` \| `production` (controls cookie security) | Yes |
| `BACKEND_CORS_ORIGINS` | Allowed CORS origins | Yes |
| `SMTP_HOST` | Email server (optional — leave blank to disable) | No |
| `SENTRY_DSN` | Sentry error tracking (optional) | No |

See `.env.example` for the full reference with all defaults.

---

## Build Status

| Epic | Description | Status |
|---|---|---|
| **Epic 1** | Foundation, Auth & Initial Setup | In progress |
| Story 1.1 | Project scaffold (FastAPI template) | Done |
| Story 1.2 | Database schema & migrations | Done |
| Story 1.3 | Authentication backend (cookie JWT + JTI blacklist) | Done |
| Story 1.4 | Authentication frontend (login page, protected routes) | Next |
| Story 1.5 | Kite credential storage (AES-256 encrypted settings) | Pending |
| **Epic 2** | CSV Upload | Pending |
| **Epic 3** | Computation Engine | Pending |
| **Epic 4** | Portfolio View | Pending |
| **Epic 5** | Stock Analysis | Pending |
| **Epic 6** | User Management | Pending |

---

## The Framework (brief)

The Multi-Layer Capital Allocation System v3.0 evaluates each Nifty 50 stock across:

- **9 weighted factors** grouped into 3 lenses: Valuation, Earnings Quality, Liquidity/Momentum
- **Regime detection** — macro regime (RBI rate cycle, credit growth) modulates factor weights
- **Decision Signal** — derived from composite score + Momentum ROC + Asymmetry Index (−Valuation + Earnings + Liquidity)
- **3-layer position sizing** — Base allocation × Conviction multiplier (score strength) × Volatility adjustment (relative to Nifty 50)
- **Time Stop** — months held without meaningful price movement, flags stale positions

The framework weights are hardcoded. The app provides clarity, not configurability.

---

## Security Notes

- JWT tokens are stored in httpOnly cookies — never in localStorage or JavaScript state
- Server-side logout via JTI blacklist — token is immediately invalidated on logout
- Kite API credentials encrypted at rest with AES-256
- No secrets committed to source control — environment variable injection only
- HTTPS enforced in production via Traefik TLS termination

---

## License

Private repository. All rights reserved.
