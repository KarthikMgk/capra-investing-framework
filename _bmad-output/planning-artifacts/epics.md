---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics']
inputDocuments: ['_bmad-output/planning-artifacts/prd.md', '_bmad-output/planning-artifacts/architecture.md']
---

# Capra Investing Framework - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for the Capra Investing Framework, decomposing the requirements from the PRD and Architecture into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: Users can authenticate with email and password
FR2: Authenticated users can log out with immediate session invalidation
FR3: Unauthenticated users accessing any protected route are redirected to login
FR4: The system enforces role-based capabilities — Admin has full access; Viewer has read-only access
FR5: Authentication tokens expire after 24 hours and require re-authentication
FR6: Users can view all holdings (name, quantity, live price) pulled from their Kite Connect account
FR7: Users can see the current signal badge for each holding in the portfolio view
FR8: Users can navigate from any holding to the full stock analysis screen for that stock
FR9: Users can search for any Nifty 50 stock by name or ticker from a pre-loaded list
FR10: Users can view the weighted composite score (−1 to +1) for a selected stock
FR11: Users can view the 5-state decision signal for a selected stock
FR12: Users can view the recommended position size for a selected stock
FR13: Users can expand the Score pillar to view all 9 weighted factors with individual signals and weighted contributions
FR14: Users can expand the Signal pillar to view conditions that triggered the current signal, ROC value, Asymmetry Index value, and Time Stop indicator (months held without meaningful movement)
FR15: Users can expand the Position Size pillar to view the step-by-step calculation (Base → Conviction → Volatility → Final) with risk control reminders (max 10–15% single stock, 10–20% cash reserve)
FR16: Users can see the timestamp of when the displayed score was last computed
FR17: Users can see separate freshness indicators for automated data (Kite Connect) and manual data (CSV uploads)
FR18: Admin users can trigger a data refresh that re-pulls all Kite Connect data and recomputes all framework scores
FR19: Viewer users cannot trigger data refresh
FR20: The system computes a weighted composite score across 9 factors for any Nifty 50 stock
FR21: The system computes Momentum ROC using 3-month historical price data from Kite Connect
FR22: The system computes the Asymmetry Index (−Valuation + Earnings + Liquidity)
FR23: The system determines the 5-state decision signal using Score, Momentum, and Asymmetry per the decision matrix
FR24: The system computes 3-layer position sizing (Base × Conviction × Volatility) per the framework
FR25: The system computes relative strength for any stock against the Nifty 50 over a 6-month window
FR26: The system computes the Time Stop indicator (months elapsed since stock showed meaningful price movement)
FR27: The system records which data snapshot (Kite timestamp + CSV upload dates) was used for each score computation
FR28: Admin users can upload a Screener.in CSV containing Nifty 50 fundamentals and earnings data
FR29: Admin users can upload an RBI macro CSV containing repo rate, credit growth, and liquidity indicators
FR30: The system validates uploaded CSV files against expected column schemas before accepting them
FR31: The system provides descriptive error messages identifying missing or mismatched columns when validation fails
FR32: Invalid CSV files are rejected without modifying existing stored data
FR33: Successfully validated CSV data atomically replaces the previous version of that data type
FR34: Viewer users cannot upload data
FR35: Admin users can create user accounts with assigned roles (Admin or Viewer)
FR36: Admin users can view all existing user accounts
FR37: Admin users can deactivate or remove user accounts
FR38: The system stores Kite Connect API credentials encrypted at rest
FR39: The system enforces HTTPS for all client-server communication
FR40: The system processes uploaded CSV files in memory for validation before writing to persistent storage

### NonFunctional Requirements

NFR1: Portfolio view loads with live quotes within 2 seconds of page render
NFR2: Refresh cycle (Kite data pull + all Nifty 50 score recomputations) completes within 3 seconds
NFR3: CSV upload validation feedback appears within 500ms of file selection
NFR4: Stock analysis screen renders cached scores within 1 second of stock selection
NFR5: Production React bundle under 200KB gzipped — Tailwind purged, code-split by route
NFR6: All client-server communication uses HTTPS/TLS 1.2+ — no HTTP fallback
NFR7: Kite Connect API key and access token stored encrypted at rest (AES-256) — never in plaintext
NFR8: JWT access tokens expire within 24 hours; invalidated server-side on logout
NFR9: All API endpoints validate JWT and enforce role permissions on every request
NFR10: CSV file contents never written to disk in unvalidated state — memory-only until validation passes
NFR11: No sensitive credentials committed to source control — environment variable injection only
NFR12: User passwords hashed with bcrypt minimum cost factor 12
NFR13: Kite Connect API calls use the official `kiteconnect` Python library
NFR14: Kite Connect API responses validated for expected schema before entering the computation layer — malformed responses raise handled errors, not silent wrong scores
NFR15: Computation engine decoupled from Kite Connect client — fully testable with mock data without live API credentials

### Additional Requirements

- **Starter Template Init**: Clone the Full Stack FastAPI Template (`git clone https://github.com/fastapi/full-stack-fastapi-template`) as the project foundation; adapt for single-process deployment; this is the first implementation story
- **StaticFiles Mount Order**: In `main.py`, API router (`include_router`) MUST be registered before `app.mount("/", StaticFiles(...))` — reversing this silently routes all API calls to the SPA
- **JTI Blacklist Setup**: Create `revoked_tokens` table with indexed `jti` column; on every successful login, delete expired rows (`expires_at < NOW()`) to prevent unbounded growth
- **factor_breakdown JSONB Schema**: Computation engine output must exactly match the defined schema: `factors` array (all 9 items with `name`, `weight`, `raw_value`, `weighted_contribution`, `signal`), plus `roc`, `asymmetry_index`, `time_stop_months`, `position_breakdown` (`base_pct`, `conviction_multiplier`, `volatility_adjustment`, `final_pct`)
- **Cookie Configuration Per Environment**: JWT httpOnly cookie must set `Secure=False, SameSite=Lax` for local dev (HTTP) and `Secure=True, SameSite=Strict` for production (HTTPS)
- **Axios `withCredentials: true`**: The Axios instance in `apiClient.ts` must set `withCredentials: true` globally — required for httpOnly cookies to be sent with every API request
- **Alembic Migrations First**: DB schema must be established via Alembic before any other backend work; first migration creates all 5 tables: `users`, `score_snapshots`, `screener_data`, `rbi_macro_data`, `revoked_tokens`
- **Docker Compose for Local Dev**: Local development runs via `docker-compose up` (postgres + backend with uvicorn --reload + frontend with vite dev server); production uses Nginx → Gunicorn → Uvicorn workers on single VPS
- **Score Snapshots Append-Only**: `score_snapshots` is append-on-refresh; UI always reads the latest row per `stock_symbol` ordered by `computation_timestamp DESC`
- **CSV Batch IDs**: `screener_data` and `rbi_macro_data` use `upload_batch_id`; computation always reads from the latest batch per type

### UX Design Requirements

No UX Design document was created for this project. UI implementation should be guided by the PRD's user journey descriptions and the component structure defined in the Architecture document.

### FR Coverage Map

FR1: Epic 1 — User login with email and password
FR2: Epic 1 — Logout with immediate session invalidation
FR3: Epic 1 — Unauthenticated users redirected to login
FR4: Epic 1 — Role-based capabilities (Admin full access, Viewer read-only)
FR5: Epic 1 — Token expiry after 24 hours + re-authentication
FR6: Epic 4 — View Kite Connect holdings with live prices
FR7: Epic 4 — Signal badge per holding in portfolio view
FR8: Epic 4 — Navigate from holding to stock analysis screen
FR9: Epic 5 — Search any Nifty 50 stock by name or ticker
FR10: Epic 5 — View weighted composite score (−1 to +1)
FR11: Epic 5 — View 5-state decision signal
FR12: Epic 5 — View recommended position size
FR13: Epic 5 — Expand Score pillar: 9 weighted factors with signals and contributions
FR14: Epic 5 — Expand Signal pillar: ROC, Asymmetry Index, Time Stop, trigger conditions
FR15: Epic 5 — Expand Position pillar: Base → Conviction → Volatility → Final with risk reminders
FR16: Epic 5 — Computation timestamp on displayed score
FR17: Epic 5 — Separate freshness indicators for Kite data vs CSV data
FR18: Epic 3 — Admin triggers full data refresh
FR19: Epic 3 — Viewer cannot trigger data refresh
FR20: Epic 3 — Weighted composite score across 9 factors
FR21: Epic 3 — Momentum ROC using 3-month historical price data
FR22: Epic 3 — Asymmetry Index (−Valuation + Earnings + Liquidity)
FR23: Epic 3 — 5-state decision signal from Score, Momentum, and Asymmetry decision matrix
FR24: Epic 3 — 3-layer position sizing (Base × Conviction × Volatility)
FR25: Epic 3 — Relative strength vs Nifty 50 over 6-month window
FR26: Epic 3 — Time Stop indicator (months without meaningful price movement)
FR27: Epic 3 — Computation audit trail: Kite snapshot ts + CSV upload dates stored per score
FR28: Epic 2 — Admin uploads Screener.in CSV (Nifty 50 fundamentals and earnings)
FR29: Epic 2 — Admin uploads RBI macro CSV (repo rate, credit growth, liquidity)
FR30: Epic 2 — CSV column schema validation before accepting upload
FR31: Epic 2 — Descriptive error messages for missing or mismatched columns
FR32: Epic 2 — Invalid CSV rejected without modifying existing stored data
FR33: Epic 2 — Valid CSV atomically replaces previous version of that data type
FR34: Epic 2 — Viewer cannot upload data
FR35: Epic 6 — Admin creates user accounts with role assignment
FR36: Epic 6 — Admin views all existing user accounts
FR37: Epic 6 — Admin deactivates or removes user accounts
FR38: Epic 1 — Kite Connect API credentials stored encrypted at rest (AES-256)
FR39: Epic 1 — HTTPS enforced for all client-server communication
FR40: Epic 2 — CSV files processed in memory for validation before writing to storage

## Epic List

### Epic 1: Foundation, Auth & Initial Setup
Users can securely log in, access role-appropriate screens, and (as admin) configure Kite Connect credentials — the essential prerequisite before any data flows.
**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR38, FR39
**NFRs:** NFR5, NFR6, NFR8, NFR9, NFR11, NFR12
**Additional requirements:** Starter template init (Full Stack FastAPI Template), Docker Compose local dev, Alembic migrations for all 5 tables, StaticFiles mount order constraint, JTI blacklist with login-time cleanup, cookie config per environment (dev vs prod), Axios `withCredentials: true` globally

### Epic 2: CSV Data Upload
Admin can upload Screener.in and RBI macro CSVs with real-time column validation, descriptive errors, and atomic replacement — providing the fresh fundamental and macro data the computation engine needs.
**FRs covered:** FR28, FR29, FR30, FR31, FR32, FR33, FR34, FR40
**NFRs:** NFR3, NFR10
**Additional requirements:** Memory-only CSV validation (bytes input), `upload_batch_id` on all CSV rows, computation reads latest batch per type

### Epic 3: Computation Engine & Data Refresh
Admin can trigger a full refresh that pulls Kite Connect data, runs all 6 framework computations for 50 stocks in under 3 seconds, and caches scored results with a complete audit trail.
**FRs covered:** FR18, FR19, FR20, FR21, FR22, FR23, FR24, FR25, FR26, FR27
**NFRs:** NFR2, NFR13, NFR14, NFR15
**Additional requirements:** asyncio.gather for I/O phase + ThreadPoolExecutor for CPU phase, pure computation functions (no I/O), `factor_breakdown` JSONB schema (factors array + roc + asymmetry_index + time_stop_months + position_breakdown), score_snapshots append-only (latest per stock_symbol)

### Epic 4: Portfolio View
Users can see all Kite Connect holdings on a single screen with live prices and signal badges, and navigate directly to any stock's full analysis.
**FRs covered:** FR6, FR7, FR8
**NFRs:** NFR1

### Epic 5: Stock Analysis — Decision Cockpit
Users can search any Nifty 50 stock and see the complete framework answer (Score, Signal, Position Size) with full expandable breakdowns and separate data freshness indicators.
**FRs covered:** FR9, FR10, FR11, FR12, FR13, FR14, FR15, FR16, FR17
**NFRs:** NFR4

### Epic 6: User Management
Admin can create, view, and deactivate user accounts with role assignment so trusted people can access the app with appropriate permissions.
**FRs covered:** FR35, FR36, FR37

<!-- Repeat for each epic in epics_list (N = 1, 2, 3...) -->

## Epic {{N}}: {{epic_title_N}}

{{epic_goal_N}}

<!-- Repeat for each story (M = 1, 2, 3...) within epic N -->

### Story {{N}}.{{M}}: {{story_title_N_M}}

As a {{user_type}},
I want {{capability}},
So that {{value_benefit}}.

**Acceptance Criteria:**

<!-- for each AC on this story -->

**Given** {{precondition}}
**When** {{action}}
**Then** {{expected_outcome}}
**And** {{additional_criteria}}

<!-- End story repeat -->
