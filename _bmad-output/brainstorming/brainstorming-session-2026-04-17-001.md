---
stepsCompleted: [1, 2, 3]
inputDocuments: [capra-framework]
session_topic: 'Building the Capra Investing Framework App — Indian stock market entry/exit decision tool'
session_goals: 'Assess feasibility, define app architecture, determine API strategy, and ideate on features for a minimal-UI, functional investing app based on the Multi-Layer Capital Allocation System v3.0'
selected_approach: 'ai-recommended'
techniques_used: ['Question Storming', 'Morphological Analysis', 'Reverse Brainstorming (partial)']
ideas_generated: [UI#1, UI#2, UI#3, UI#4, Architecture#1, DesignPrinciple#1]
context_file: ''
---

## Session Overview

**Topic:** Capra Investing Framework App — wrapping the Multi-Layer Capital Allocation System v3.0 into a functional, API-driven web application for Indian stock market investing decisions

**Goals:**
- Assess feasibility of full automation (no manual data ingestion)
- Define API strategy for Indian market data (price, macro, fundamentals, earnings)
- Architect for personal use now, multi-user later (auth/security included from day one)
- Minimal UI, maximum function — framework is the star

### Key Framework Facts (from capra-framework file)
- 15 factors across 8 parts
- Weighted scoring model: -1 to +1 output
- 5-state decision matrix (Aggressive Buy → Defensive)
- 3-layer position sizing model
- Monthly review cadence, regime-change driven actions

### Constraints & Decisions Captured
- **Users:** Personal now, multi-user architecture from start
- **Auth:** Full authentication + authorization built in
- **Data:** API-first, will purchase APIs — no manual ingestion
- **UI:** Minimal, functional
- **Hardest data point:** Expectation Gap (earnings surprise + price reaction) — solvable with paid API

### Session Setup
User has a complete, institutional-grade framework ready. The task is to build the app around it, not design the framework. Sensible defaults preferred — no time wasted on trivial decisions.

---

## Technique Execution Results

### Phase 1: Question Storming — Key Decisions

**UX Flow:** Search bar → select Nifty 50 stock → 3-pillar hero analysis page
**Tool type:** Check-it-act + monitor-and-observe hybrid
**Upload validation:** Real-time, before upload completes — reject with clear error message

### Phase 2: Morphological Analysis — Full App Map

**Screens:**
1. Login — JWT auth, multi-user ready
2. Portfolio — Kite Connect holdings, live quotes, signal badge per stock
3. Stock Search + Analysis — Nifty 50 only, 3-pillar hero, expandable detail
4. Data Upload — CSV for RBI + Screener with real-time validation

**Computations:**
1. Weighted Score (9 factors → −1 to +1)
2. Momentum ROC (price 3M ago vs today)
3. Asymmetry Index (−Valuation + Earnings + Liquidity)
4. Decision Signal (5-state)
5. Position Size (Base × Conviction × Volatility)
6. Relative Strength (stock vs Nifty 6M)

**Data Stack:**
- Kite Connect → prices, holdings, indices, USD/INR, Gold (API, on refresh)
- Screener.in → fundamentals + earnings (manual CSV, monthly)
- RBI website → macro data (manual CSV, monthly / per MPC meeting)
- NSE website → Nifty PE/PB (automated)

**Tech Stack:**
- Frontend: React + Tailwind
- Backend: Python FastAPI
- Database: PostgreSQL
- Auth: JWT
- Hosting: Single VPS (DigitalOcean)
- Kite SDK: kiteconnect Python library

**User Roles:**
- Admin: upload CSVs, manage users, refresh data
- Viewer: search stocks, view analysis, view portfolio

**Architecture:**
- Pre-computed scores cached until user hits refresh
- Refresh = pull latest Kite data + rerun all 6 computations + update cache
- Holdings pulled directly from Kite Connect (no manual input)

### Key Design Decisions Captured

| # | Decision |
|---|---|
| UI#1 | 3-pillar hero: Score / Signal / Position Size — click to expand detail |
| UI#2 | Timestamp on each box + single refresh button (automated vs manual data shown separately) |
| UI#3 | Search bar: Nifty 50 stocks only, selection list (no free text) |
| UI#4 | Portfolio: stock name + quantity + live price + signal badge |
| Architecture#1 | Pull + cache model — pre-computed, refreshed on demand |
| Design#1 | Light mode only, no dark mode, no animations, no clutter |

### Box Detail Panels (Sensible Defaults)

**Box 1 — Score expanded:** Table of 9 factors with weight, raw signal (↑/→/↓), and weighted contribution. Color coded green/amber/red.

**Box 2 — Signal expanded:** Conditions met that triggered signal (checkmarks), ROC value, Asymmetry Index value, "what would change this signal" note.

**Box 3 — Position Size expanded:** Step-by-step: Base Allocation → Conviction Multiplier → Volatility Adjustment → Final %. Risk control reminders (max 10–15% single stock, 10–20% cash).

### MVP Scope — Final

Build this. Nothing more.
- 4 screens: Login, Portfolio, Stock Analysis, Data Upload
- Kite Connect for all market data + holdings
- Manual CSV uploads for RBI + Screener
- React + FastAPI + PostgreSQL + JWT
- Light mode, minimal, functional
