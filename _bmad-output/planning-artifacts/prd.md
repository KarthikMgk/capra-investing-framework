---
stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-02b-vision', 'step-02c-executive-summary', 'step-03-success', 'step-04-journeys', 'step-05-domain', 'step-06-innovation', 'step-07-project-type', 'step-08-scoping', 'step-09-functional', 'step-10-nonfunctional', 'step-11-polish', 'step-12-complete']
inputDocuments: ['_bmad-output/brainstorming/brainstorming-session-2026-04-17-001.md', 'capra-framework']
workflowType: 'prd'
classification:
  projectType: web_app
  domain: fintech
  complexity: high
  projectContext: greenfield
---

# Product Requirements Document — Capra Investing Framework App

**Author:** Karthikmg
**Date:** 2026-04-17

---

## Executive Summary

Capra is a personal web application that operationalises the Multi-Layer Capital Allocation System v3.0 — a 15-factor, regime-based framework for determining entry, exit, and position sizing decisions on Nifty 50 stocks in the Indian equity market. The app serves a single primary user (with multi-user architecture built in from day one) — replacing manual spreadsheet evaluation with an automated, data-driven cockpit.

**The problem:** A sophisticated framework exists but running it manually is slow, error-prone, and creates friction that reduces discipline. The app eliminates that friction — search a stock, hit refresh, get the answer.

**Target user:** A disciplined retail investor operating the Capra framework on Indian equities, requiring monthly-cadence analysis with on-demand refresh capability.

**Core differentiator:** A 3-pillar decision surface (Score / Signal / Position Size) that answers the investor's only question — *what do I do with this stock, and how much?* — in under 3 seconds. Every detail is one click away, never cluttering the primary answer.

**Key design principle:** The framework is hardcoded. The app does not offer configurability — it offers clarity.

**Data architecture:** Automated data (live prices, indices, holdings) via Kite Connect API; manual-upload data (fundamentals, macro) via validated CSV ingestion — matching data freshness to the framework's monthly review cadence.

**Innovation:** Institutional-grade capital allocation methodology (regime detection, cross-asset lenses, weighted multi-factor scoring, conviction-multiplied position sizing) delivered as a self-serve personal tool for Indian equities. The market gap: tools like Bloomberg have rigour but not accessibility; Screener/Tickertape have data but not a framework. Capra provides both for a segment that currently has neither.

## Project Classification

- **Project Type:** Web application — React SPA frontend, Python FastAPI backend
- **Domain:** Fintech — personal investment decision tooling, Indian equity markets
- **Complexity:** High — multi-source data pipeline, scoring computation engine, financial data integrity requirements, JWT-based multi-user auth
- **Project Context:** Greenfield

## Success Criteria

### User Success

- Any Nifty 50 stock search returns computed Score, Signal, and Position Size in under 3 seconds after refresh
- Portfolio view loads all holdings with live quotes and signal badges in a single screen — no navigation required
- CSV upload validates in real-time and states specifically what is wrong if rejected — zero silent failures
- The 3-pillar hero answers "what do I do?" without requiring expansion of any detail panel
- Expanding any pillar gives a complete, correct breakdown of how the answer was computed

### Business Success

- The framework replaces the manual spreadsheet entirely — no parallel spreadsheet needed post-launch
- Monthly review completes in under 10 minutes: upload CSVs → refresh → review portfolio signals → act
- Zero incorrect scores due to app computation errors

### Technical Success

- Kite Connect integration returns correct live prices, holdings, and index data on every refresh
- All 6 computations (Weighted Score, ROC, Asymmetry, Signal, Position Size, Relative Strength) match manually verified reference cases
- JWT auth enforces role separation (Admin vs Viewer) correctly across all endpoints
- CSV validator rejects malformed, mismatched-column, or corrupt files before they reach the database
- PostgreSQL cache stores and serves pre-computed scores reliably

### Measurable Outcomes

| Metric | Target |
|---|---|
| Refresh-to-result | < 3 seconds |
| Upload validation feedback | < 500ms |
| Portfolio load | < 2 seconds |
| Stock analysis render (cached) | < 1 second |
| Score computation accuracy | 100% match vs. reference cases |

## Project Scope & Phased Development

### MVP Strategy

**Approach:** Problem-solving MVP — the minimum that completely replaces the manual spreadsheet workflow. No new features until the core loop (upload → refresh → analyse → decide) works flawlessly.

**Resource model:** Solo developer or small team. Single VPS, single codebase, no microservices.

**Tech stack:** React + Tailwind · Python FastAPI · PostgreSQL · JWT · DigitalOcean Mumbai

### Phase 1 — MVP

**Screens:**
- Login (JWT auth, Admin + Viewer roles)
- Portfolio view (holdings from Kite Connect, live quotes, signal badge per stock)
- Stock search + analysis (Nifty 50 only, 3-pillar hero, click-to-expand detail panels)
- Data upload (RBI CSV + Screener CSV, real-time column validation)
- Admin settings (create/manage user accounts)

**Computations:** Weighted Score, ROC, Asymmetry Index, Decision Signal, Position Size, Relative Strength

**Data integrations:** Kite Connect (prices, indices, USD/INR, Gold, holdings) + manual CSV uploads (Screener fundamentals + RBI macro)

### Phase 2 — Growth

- Score history chart per stock
- Signal change alerts (email/push)
- Nifty Next 50 or broader NSE coverage
- Multi-user self-registration onboarding

### Phase 3 — Expansion

- User-configurable framework weights
- Backtesting engine against historical data
- Portfolio optimisation layer
- Mobile-optimised layout

### Scope Risk Mitigations

- **Technical:** Kite Connect data mapping validated against manually computed reference cases before launch
- **Scope creep:** MVP is locked by this document — nothing added until Phase 1 ships
- **Resource:** Lean stack with no exotic dependencies; clear screen-by-screen build order

## User Journeys

### Journey 1: Admin — Monthly Review (Happy Path)

Karthik opens Capra on the first Sunday of the month. He logs in, lands on Portfolio view — 8 holdings, each with a live quote and signal badge. Three green (Accumulate), four white (Hold), one red (Reduce). The shape of his next action is visible in 5 seconds without reading a number.

He drops this month's Screener export and RBI CSV into the Upload screen. Both validate instantly. Back to portfolio — he clicks **Refresh**. In under 3 seconds, all scores recompute. He taps HDFC Bank: Score +0.61, Signal 🟡 Early Accumulate, Position 65% base × 1.5x conviction. He expands the Score pillar — Relative Strength is the drag factor. Decision: add a modest position now, not full allocation. Review done in under 10 minutes.

**Capabilities:** Login, Portfolio view, CSV upload + validation, Refresh, Stock analysis, Expandable factor breakdown.

### Journey 2: Admin — Bad CSV Upload (Edge Case)

Karthik uploads a Screener export where a column was renamed. Instantly: *"Column 'PE_Ratio' not found. Expected: PE_Ratio, PB_Ratio, EPS_Growth, Earnings_Surprise."* File not saved. Existing data intact. He fixes the export, re-uploads, gets a clean validation, refreshes.

**Capabilities:** Real-time column validation, descriptive error messages, no partial saves, existing data preservation.

### Journey 3: Viewer — Stock Lookup

A trusted friend with Viewer access logs in, lands on read-only Portfolio view, navigates to Stock Search, types "Inf", selects Infosys. Score +0.38, Signal ⚪ Hold, Position 30% base. He expands the Signal pillar — Score improving but Momentum hasn't turned. He has what he needed.

**Capabilities:** Role-based access (Viewer cannot refresh/upload), read-only analysis, Nifty 50 search, signal detail panel.

### Journey 4: Admin — User Management

Karthik navigates to Settings, creates a Viewer account for his brother with email and temporary password. His brother logs in and lands on the read-only Portfolio view.

**Capabilities:** Admin user management, role assignment (Admin/Viewer), password management.

### Journey Requirements Summary

| Capability | Journey |
|---|---|
| JWT login with role detection | All |
| Portfolio view — live quotes + signal badges | 1, 3 |
| CSV upload with real-time column validation | 1, 2 |
| Refresh → recompute all scores | 1 |
| Nifty 50 stock search | 1, 3 |
| 3-pillar hero + expandable detail panels | 1, 3 |
| Role-based access control (Admin vs Viewer) | 3 |
| Admin user management screen | 4 |
| Descriptive upload errors, no partial saves | 2 |

## Domain-Specific Requirements

### Compliance & Regulatory

- **No transaction processing** — app provides analysis only; does not execute or route orders. SEBI investment advisor regulations do not apply (personal use, no fee-based advice to third parties).
- **Kite Connect API ToS** — Zerodha's terms permit personal analysis use; data redistribution is prohibited.
- **Data localisation** — all user data and market data must remain on India-hosted infrastructure (DigitalOcean Mumbai region or equivalent).

### Data Integrity

- **Computation audit trail** — each score computation stores which data version was used (Kite snapshot timestamp + CSV upload dates) to enable diagnosis of wrong scores.
- **No silent data overwrites** — CSV uploads replace existing data only after successful validation, atomically.
- **Wrong score mitigation** — all 6 computations validated against manually computed reference cases before launch; user-controlled refresh prevents silent recomputation.
- **Stale data visibility** — timestamp on each pillar box; separate freshness indicator for automated (Kite) vs. manual (CSV) data.

## Web Application Requirements

### Architecture

- **Type:** SPA — React handles all routing client-side. FastAPI serves the built React bundle and all `/api/` routes from a single server.
- **Auth boundary:** All routes protected — unauthenticated requests redirect to login.
- **Real-time:** Not required — data freshness is user-triggered. No WebSockets, polling, or SSE.
- **SEO:** Not required — no public pages, no indexing.

### Browser Support

| Browser | Support |
|---|---|
| Chrome (latest 2) | ✅ Primary |
| Safari (latest 2) | ✅ |
| Firefox (latest 2) | ✅ |
| Edge (latest 2) | ✅ |
| IE / Legacy | ❌ |

### Responsive Design

- **Primary target:** Desktop/laptop (1280px+)
- **Tablet:** Acceptable degradation, no dedicated layout
- **Mobile:** Not targeted for MVP

### Implementation Decisions

- React Router — protected routes, redirect to login on missing/expired JWT
- Tailwind CSS — utility-first, no component library overhead, purged in production
- Axios — JWT interceptor auto-attaches token to every API request
- Single deployment unit — FastAPI serves React build; no separate CDN for MVP
- Accessibility: WCAG 2.1 Level A minimum — standard HTML semantics, keyboard navigability

## Functional Requirements

### Authentication & Access Control

- **FR1:** Users can authenticate with email and password
- **FR2:** Authenticated users can log out with immediate session invalidation
- **FR3:** Unauthenticated users accessing any protected route are redirected to login
- **FR4:** The system enforces role-based capabilities — Admin has full access; Viewer has read-only access
- **FR5:** Authentication tokens expire after 24 hours and require re-authentication

### Portfolio Management

- **FR6:** Users can view all holdings (name, quantity, live price) pulled from their Kite Connect account
- **FR7:** Users can see the current signal badge for each holding in the portfolio view
- **FR8:** Users can navigate from any holding to the full stock analysis screen for that stock

### Stock Search & Analysis

- **FR9:** Users can search for any Nifty 50 stock by name or ticker from a pre-loaded list
- **FR10:** Users can view the weighted composite score (−1 to +1) for a selected stock
- **FR11:** Users can view the 5-state decision signal for a selected stock
- **FR12:** Users can view the recommended position size for a selected stock
- **FR13:** Users can expand the Score pillar to view all 9 weighted factors with individual signals and weighted contributions
- **FR14:** Users can expand the Signal pillar to view conditions that triggered the current signal, ROC value, Asymmetry Index value, and Time Stop indicator (months held without meaningful movement)
- **FR15:** Users can expand the Position Size pillar to view the step-by-step calculation (Base → Conviction → Volatility → Final) with risk control reminders (max 10–15% single stock, 10–20% cash reserve)
- **FR16:** Users can see the timestamp of when the displayed score was last computed
- **FR17:** Users can see separate freshness indicators for automated data (Kite Connect) and manual data (CSV uploads)

### Data Refresh & Computation

- **FR18:** Admin users can trigger a data refresh that re-pulls all Kite Connect data and recomputes all framework scores
- **FR19:** Viewer users cannot trigger data refresh
- **FR20:** The system computes a weighted composite score across 9 factors for any Nifty 50 stock
- **FR21:** The system computes Momentum ROC using 3-month historical price data from Kite Connect
- **FR22:** The system computes the Asymmetry Index (−Valuation + Earnings + Liquidity)
- **FR23:** The system determines the 5-state decision signal using Score, Momentum, and Asymmetry per the decision matrix
- **FR24:** The system computes 3-layer position sizing (Base × Conviction × Volatility) per the framework
- **FR25:** The system computes relative strength for any stock against the Nifty 50 over a 6-month window
- **FR26:** The system computes the Time Stop indicator (months elapsed since stock showed meaningful price movement)
- **FR27:** The system records which data snapshot (Kite timestamp + CSV upload dates) was used for each score computation

### Data Ingestion & Upload

- **FR28:** Admin users can upload a Screener.in CSV containing Nifty 50 fundamentals and earnings data
- **FR29:** Admin users can upload an RBI macro CSV containing repo rate, credit growth, and liquidity indicators
- **FR30:** The system validates uploaded CSV files against expected column schemas before accepting them
- **FR31:** The system provides descriptive error messages identifying missing or mismatched columns when validation fails
- **FR32:** Invalid CSV files are rejected without modifying existing stored data
- **FR33:** Successfully validated CSV data atomically replaces the previous version of that data type
- **FR34:** Viewer users cannot upload data

### User Management

- **FR35:** Admin users can create user accounts with assigned roles (Admin or Viewer)
- **FR36:** Admin users can view all existing user accounts
- **FR37:** Admin users can deactivate or remove user accounts

### Security & Data Integrity

- **FR38:** The system stores Kite Connect API credentials encrypted at rest
- **FR39:** The system enforces HTTPS for all client-server communication
- **FR40:** The system processes uploaded CSV files in memory for validation before writing to persistent storage

## Non-Functional Requirements

### Performance

- **NFR1:** Portfolio view loads with live quotes within 2 seconds of page render
- **NFR2:** Refresh cycle (Kite data pull + all Nifty 50 score recomputations) completes within 3 seconds
- **NFR3:** CSV upload validation feedback appears within 500ms of file selection
- **NFR4:** Stock analysis screen renders cached scores within 1 second of stock selection
- **NFR5:** Production React bundle under 200KB gzipped — Tailwind purged, code-split by route

### Security

- **NFR6:** All client-server communication uses HTTPS/TLS 1.2+ — no HTTP fallback
- **NFR7:** Kite Connect API key and access token stored encrypted at rest (AES-256 or equivalent) — never in plaintext
- **NFR8:** JWT access tokens expire within 24 hours; invalidated server-side on logout
- **NFR9:** All API endpoints validate JWT and enforce role permissions on every request
- **NFR10:** CSV file contents never written to disk in unvalidated state — memory-only until validation passes
- **NFR11:** No sensitive credentials (API keys, DB passwords) committed to source control — environment variable injection only
- **NFR12:** User passwords hashed with bcrypt (minimum cost factor 12)

### Integration

- **NFR13:** Kite Connect API calls use the official `kiteconnect` Python library
- **NFR14:** Kite Connect API responses validated for expected schema before entering the computation layer — malformed responses raise handled errors, not silent wrong scores
- **NFR15:** Computation engine decoupled from Kite Connect client — fully testable with mock data without live API credentials
