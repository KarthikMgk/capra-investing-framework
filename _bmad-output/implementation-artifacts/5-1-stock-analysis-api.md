# Story 5.1: Stock Analysis API

Status: ready-for-dev

## Story

As an authenticated user,
I want to search and retrieve complete stock analysis data from the backend,
so that the stock analysis screen can display composite scores, signals, position sizes, and factor breakdowns served from the score cache.

## Acceptance Criteria

1. **Given** an authenticated user calls `GET /api/v1/stocks`, **When** the request is processed, **Then** the response is `{ "items": [...], "total": 50 }` containing all 50 Nifty 50 symbols, each with `stock_symbol`, `name`, and `signal` (null if no snapshot exists).

2. **Given** an authenticated user calls `GET /api/v1/stocks/HDFCBANK` and a score snapshot exists for HDFCBANK, **When** the request is processed, **Then** the response returns HTTP 200 with a full `StockScoreResponse` including `composite_score`, `signal`, `position_size`, `computation_timestamp`, `kite_snapshot_ts`, `screener_csv_ts`, `rbi_csv_ts`, and a non-null `factor_breakdown` object.

3. **Given** the `factor_breakdown` field in the response, **When** it is inspected, **Then** it contains a `factors` array with exactly 9 items each having `name`, `weight`, `raw_value`, `weighted_contribution`, and `signal` fields, plus top-level `roc`, `asymmetry_index`, `time_stop_months`, and `position_breakdown` (`base_pct`, `conviction_multiplier`, `volatility_adjustment`, `final_pct`).

4. **Given** an authenticated user calls `GET /api/v1/stocks/HDFCBANK` and NO snapshot exists for HDFCBANK, **When** the request is processed, **Then** the response returns HTTP 404 with body `{"error": {"code": "SCORE_NOT_FOUND", "message": "No score computed for HDFCBANK. Run a data refresh first."}}`.

5. **Given** an unauthenticated request to `GET /api/v1/stocks` or `GET /api/v1/stocks/{stock_symbol}`, **When** the request is processed, **Then** the response is HTTP 401.

6. **Given** a Viewer-role user calls `GET /api/v1/stocks` or `GET /api/v1/stocks/{stock_symbol}`, **When** the request is processed, **Then** the response returns HTTP 200 — these are read endpoints accessible to all authenticated users.

7. **Given** `GET /api/v1/stocks/{stock_symbol}` is called with a valid symbol, **When** the query executes, **Then** a single `SELECT` from `score_snapshots` is performed with no live Kite Connect call — satisfying NFR4 (cached analysis renders in < 1 second).

8. **Given** `GET /api/v1/stocks` is called, **When** the response is received, **Then** every item includes `name` (human-readable stock name), not just `stock_symbol` — enabling typeahead search by name or symbol on the frontend.

9. **Given** the stock endpoint responses, **When** any JSON field is inspected, **Then** all field names are `snake_case` — never `camelCase`.

## Tasks / Subtasks

- [ ] Task 1: Create `backend/app/api/v1/stocks.py` — stock list and stock detail endpoints (AC: 1, 2, 4, 5, 6, 7, 8)
  - [ ] Define `GET /api/v1/stocks` with `Depends(get_current_user)`:
    - Iterate over `NIFTY_50_SYMBOLS` constant from `core/constants.py`
    - For each symbol, query `score_snapshots WHERE stock_symbol = ? ORDER BY computation_timestamp DESC LIMIT 1` (or a single batch query)
    - Build `StockListItem { stock_symbol: str, name: str, signal: str | None }` for each symbol
    - Return `{ "items": [...], "total": 50 }` — all 50 symbols always present, `signal` is null if no snapshot
  - [ ] Define `GET /api/v1/stocks/{stock_symbol}` with `Depends(get_current_user)`:
    - Query `SELECT * FROM score_snapshots WHERE stock_symbol = :symbol ORDER BY computation_timestamp DESC LIMIT 1`
    - If no row found: raise `HTTPException(status_code=404, detail={"error": {"code": "SCORE_NOT_FOUND", "message": f"No score computed for {stock_symbol}. Run a data refresh first."}})`
    - Return full `StockScoreResponse` from the snapshot row — return `factor_breakdown` JSONB as-is, no re-parsing
  - [ ] Register the stocks router in `backend/app/main.py` or `backend/app/api/v1/__init__.py`

- [ ] Task 2: Extend `backend/app/schemas/stock.py` — add missing schema types (AC: 2, 3, 8, 9)
  - [ ] This file was created in Story 3.1 (computation engine) — EXTEND it, do not re-create
  - [ ] Add `StockListItem { stock_symbol: str, name: str, signal: str | None }`
  - [ ] Verify `StockScoreResponse` includes all fields: `stock_symbol`, `composite_score`, `signal`, `position_size`, `computation_timestamp`, `kite_snapshot_ts`, `screener_csv_ts`, `rbi_csv_ts`, `factor_breakdown`
  - [ ] Add `FactorItem { name: str, weight: float, raw_value: float, weighted_contribution: float, signal: str }` if not present
  - [ ] Add `PositionBreakdown { base_pct: float, conviction_multiplier: float, volatility_adjustment: float, final_pct: float }` if not present
  - [ ] Add `FactorBreakdown { factors: list[FactorItem], roc: float, asymmetry_index: float, time_stop_months: int, position_breakdown: PositionBreakdown }` if not present
  - [ ] All field names `snake_case`

- [ ] Task 3: Verify `NIFTY_50_SYMBOLS` constant and name mapping exist in `backend/app/core/constants.py` (AC: 1, 8)
  - [ ] Confirm `NIFTY_50_SYMBOLS` is a list or dict of all 50 symbols (established in Epic 3)
  - [ ] Ensure a `NIFTY_50_NAMES` mapping or equivalent structure provides the human-readable name for each symbol (e.g., `{"HDFCBANK": "HDFC Bank Limited", ...}`)
  - [ ] If the name mapping does not yet exist, add it to `constants.py` — the stock list endpoint needs names for typeahead

- [ ] Task 4: Write `backend/app/tests/test_api_stocks.py` (AC: 1, 2, 3, 4, 5)
  - [ ] Test: `GET /api/v1/stocks` returns 50 items — verify `len(response["items"]) == 50`
  - [ ] Test: `GET /api/v1/stocks/HDFCBANK` with an existing snapshot returns HTTP 200 with full response including non-null `factor_breakdown`
  - [ ] Test: `factor_breakdown` response matches exact schema — `factors` array has 9 items, each with `name`, `weight`, `raw_value`, `weighted_contribution`, `signal`; top-level keys `roc`, `asymmetry_index`, `time_stop_months`, `position_breakdown` all present
  - [ ] Test: `GET /api/v1/stocks/HDFCBANK` with no snapshot returns HTTP 404 with `{"error": {"code": "SCORE_NOT_FOUND", ...}}`
  - [ ] Test: Unauthenticated request to `GET /api/v1/stocks` returns HTTP 401
  - [ ] Test: Unauthenticated request to `GET /api/v1/stocks/HDFCBANK` returns HTTP 401
  - [ ] Use `conftest.py` fixtures for test DB, mock auth cookie, and seeded score snapshot data

## Dev Notes

- **Single SELECT query — NO live Kite call on read path:** `GET /api/v1/stocks/{stock_symbol}` MUST query only `score_snapshots`. It must never call `kite_client` or any other I/O service. This is the architectural guarantee for NFR4 (< 1 second response). Any live data fetch on this path violates the performance requirement.
- **`factor_breakdown` is JSONB — return as-is:** The `factor_breakdown` column is stored as JSONB in PostgreSQL. When building the response, return the JSONB value directly as a Python `dict`. Do not re-parse, re-compute, or validate its structure on the read path. The computation engine (Epic 3) is responsible for writing the correct schema.
- **`GET /api/v1/stocks` must include `name`:** This endpoint powers the frontend typeahead search. If `name` is missing, users cannot search by company name (FR9). Use `NIFTY_50_NAMES` constant or equivalent mapping.
- **All JSON field names `snake_case`:** `stock_symbol`, `composite_score`, `kite_snapshot_ts`, `screener_csv_ts`, `rbi_csv_ts`, `factor_breakdown` — never `stockSymbol`, `compositeScore`, `kiteSnapshotTs`. FastAPI/Pydantic defaults match this convention.
- **404 error envelope shape (exact):** `{"error": {"code": "SCORE_NOT_FOUND", "message": "No score computed for HDFCBANK. Run a data refresh first."}}` — use the symbol name in the message for clarity. Use `HTTPException` at the router layer only; do not raise from a service.
- **`score_snapshots` is append-only, always read latest:** Always query with `ORDER BY computation_timestamp DESC LIMIT 1`. Never assume there is only one row per symbol.
- **`backend/app/schemas/stock.py` already exists:** This file was created in Story 3.1. Use `# extend` comments to add new schema classes — do not overwrite existing content.
- **Viewer role has READ access to stock endpoints:** `GET /api/v1/stocks` and `GET /api/v1/stocks/{stock_symbol}` use `Depends(get_current_user)`, NOT `Depends(require_admin)`. Both Admin and Viewer can read stock data.
- **Test fixtures:** The `conftest.py` in `backend/app/tests/` (created in Story 1.2) provides the test DB session. Add fixtures for seeding a `ScoreSnapshot` row and for authenticated test client with admin and viewer roles. The first admin user is seeded from Story 1.1's `FIRST_SUPERUSER_EMAIL`.
- **`factor_breakdown` exact schema (from architecture.md Gap Analysis):**
  ```json
  {
    "factors": [
      {"name": "relative_strength", "weight": 0.15, "raw_value": 0.72, "weighted_contribution": 0.108, "signal": "positive"}
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
  The `factors` array must have exactly 9 items. The test must verify this count.

### Project Structure Notes

- Files to CREATE:
  - `backend/app/api/v1/stocks.py`
  - `backend/app/tests/test_api_stocks.py`
- Files to MODIFY:
  - `backend/app/schemas/stock.py` — extend with `StockListItem` and verify/finalize `StockScoreResponse`
  - `backend/app/core/constants.py` — add `NIFTY_50_NAMES` mapping if not present
  - `backend/app/main.py` or `backend/app/api/v1/__init__.py` — register stocks router

### References

- [Source: architecture.md#Data Architecture — Score Cache & Audit Trail]
- [Source: architecture.md#Data Flow — Stock analysis (read path)]
- [Source: architecture.md#Format Patterns — API Response Formats]
- [Source: architecture.md#Naming Patterns — JSON Field Naming Critical Rule]
- [Source: architecture.md#Gap Analysis & Resolutions — Gap 1 (factor_breakdown JSONB Schema)]
- [Source: architecture.md#Process Patterns — Backend Error Propagation]
- [Source: architecture.md#Architectural Boundaries — API Boundaries]
- [Source: epics.md#Epic 5: Stock Analysis — Decision Cockpit]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
