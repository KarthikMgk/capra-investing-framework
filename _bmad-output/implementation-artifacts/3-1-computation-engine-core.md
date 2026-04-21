# Story 3.1: Computation Engine Core

Status: ready-for-dev

## Story

As a developer,
I want all six pure computation functions implemented in `computation_engine.py` with all constants isolated in `constants.py` and a matching Pydantic schema in `schemas/stock.py`,
so that the entire computation layer is testable with mock data and satisfies 100% reference-case accuracy before any Kite Connect integration is attempted.

## Acceptance Criteria

1. **Given** `backend/app/core/constants.py` exists, **When** `FACTOR_WEIGHTS` is inspected, **Then** it contains exactly 9 entries keyed by factor name and the values sum to exactly 1.0 (verified by `test_factor_weights_sum_to_one`).

2. **Given** `backend/app/services/computation_engine.py` exists, **When** the file is statically scanned (grep) for any import from `kite_client`, `database`, `models`, or any I/O module (`requests`, `httpx`, `sqlmodel`, `sqlalchemy`), **Then** zero matches are found — the file contains only standard-library and pure-math imports.

3. **Given** the function `compute_weighted_score(factors: dict[str, float]) -> float` is called with a hand-crafted dict where every factor has a known raw value, **When** the output is compared against the expected composite score computed manually by summing `raw_value × weight` for each factor, **Then** the function result matches the expected value within `1e-6`.

4. **Given** the function `compute_roc(prices_3m: list[float]) -> float` is called with a price series whose first and last values are known, **When** the rate-of-change is computed manually as `(last - first) / first`, **Then** the function result matches the expected value within `1e-6`.

5. **Given** the function `compute_asymmetry_index(valuation_score, earnings_score, liquidity_score)` is called with known float inputs, **When** the result is compared against `(-valuation_score + earnings_score + liquidity_score)`, **Then** the function result matches within `1e-6`.

6. **Given** the function `compute_signal(composite_score, roc, asymmetry_index)` is called with inputs that map to every one of the 5 decision-matrix states, **When** the returned signal string is inspected, **Then** it is one of exactly `{"strong_buy", "buy", "hold", "sell", "strong_sell"}` and matches the expected state for each tested input set per `DECISION_MATRIX`.

7. **Given** the function `compute_position_size(signal, composite_score, volatility)` is called with a known signal and known score/volatility inputs, **When** the returned dict is inspected, **Then** it contains exactly the keys `{"base_pct", "conviction_multiplier", "volatility_adjustment", "final_pct"}`, and `final_pct` equals `base_pct × conviction_multiplier × volatility_adjustment` within `1e-6`.

8. **Given** the function `build_factor_breakdown(factors, roc, asymmetry_index, time_stop_months, position_breakdown)` is called with valid inputs, **When** the returned dict is validated against the `FactorBreakdown` Pydantic model, **Then** validation passes without error and the `factors` list contains exactly 9 items, each with keys `name`, `weight`, `raw_value`, `weighted_contribution`, and `signal`.

9. **Given** `backend/app/schemas/stock.py` contains the `FactorBreakdown` and `StockScoreResponse` models, **When** a dict matching the JSONB schema from `architecture.md#Gap Analysis — Gap 1` is passed to `FactorBreakdown(**data)`, **Then** Pydantic accepts it without raising `ValidationError`.

10. **Given** all unit tests in `backend/app/tests/test_computation_engine.py` are run with `pytest`, **When** the test run completes, **Then** every test passes (0 failures, 0 errors) — this is a launch gate.

## Tasks / Subtasks

- [ ] Task 1: Create `backend/app/core/constants.py` (AC: 1, 6, 7)
  - [ ] Define `NIFTY_50_SYMBOLS: list[str]` — the 50 ticker symbols listed on NSE as Nifty 50 constituents (e.g. `"HDFCBANK"`, `"RELIANCE"`, `"TCS"`, etc.; look up current official list)
  - [ ] Define `FACTOR_WEIGHTS: dict[str, float]` — exactly 9 entries mapping each of the 9 framework factor names to their assigned weights; values must sum to 1.0. Factor names must exactly match the keys used in `compute_weighted_score()` and appear in `build_factor_breakdown()` output. One confirmed factor name from the architecture: `"relative_strength"` with weight `0.15` (per the JSONB schema example in `architecture.md`). Research or define the remaining 8 from the project's PRD/framework spec.
  - [ ] Define `DECISION_MATRIX: dict[tuple, str]` — maps `(score_bucket: str, momentum_signal: str, asymmetry_signal: str)` → one of `{"strong_buy", "buy", "hold", "sell", "strong_sell"}`. Define the bucket boundary rules (e.g., score > 0.5 → "high", score 0.0–0.5 → "mid", score < 0.0 → "low"; equivalent logic for momentum and asymmetry). All combinations reachable in tests must be covered.
  - [ ] Define `POSITION_BASE_TABLE: dict[str, float]` — maps each of the 5 signal strings to the base position percentage (e.g., `"strong_buy"` → `65.0`; values are illustrative — confirm from framework spec)
  - [ ] Define `CONVICTION_MULTIPLIER_TABLE: list[tuple[float, float, float]]` — ordered list of `(score_low, score_high, multiplier)` tuples covering the full −1.0 to +1.0 composite score range with no gaps
  - [ ] Define `VOLATILITY_ADJUSTMENT: list[tuple[float, float, float]]` — ordered list of `(vol_low, vol_high, adjustment_factor)` tuples covering relevant beta/volatility ranges
  - [ ] Define `MEANINGFUL_MOVEMENT_THRESHOLD: float` — the percentage price change (as a decimal, e.g., `0.10` for 10%) that resets the Time Stop counter

- [ ] Task 2: Create `backend/app/services/computation_engine.py` with all 8 pure functions (AC: 2, 3, 4, 5, 6, 7, 8)
  - [ ] Import only: `from __future__ import annotations`, standard library (`math`, `typing`), and `from app.core.constants import ...` — NO kite, NO database, NO model imports
  - [ ] Implement `compute_weighted_score(factors: dict[str, float]) -> float`:
    - Iterate over `FACTOR_WEIGHTS`; for each factor key, multiply `factors[key]` by its weight; sum all contributions; return total (clamped to −1.0 to +1.0 range)
    - Raise `ValueError` if `factors` is missing any key that exists in `FACTOR_WEIGHTS`
  - [ ] Implement `compute_roc(prices_3m: list[float]) -> float`:
    - Formula: `(prices_3m[-1] - prices_3m[0]) / prices_3m[0]`
    - Raise `ValueError` if list is empty or has fewer than 2 elements
  - [ ] Implement `compute_asymmetry_index(valuation_score: float, earnings_score: float, liquidity_score: float) -> float`:
    - Formula exactly: `(-valuation_score) + earnings_score + liquidity_score`
  - [ ] Implement `compute_signal(composite_score: float, roc: float, asymmetry_index: float) -> str`:
    - Classify `composite_score` into a score bucket using constants-defined thresholds
    - Classify `roc` into a momentum signal using constants-defined thresholds
    - Classify `asymmetry_index` into an asymmetry signal using constants-defined thresholds
    - Look up `(score_bucket, momentum_signal, asymmetry_signal)` in `DECISION_MATRIX`; return the mapped signal string
    - Raise `KeyError` with a descriptive message if the combination is not in the matrix
  - [ ] Implement `compute_position_size(signal: str, composite_score: float, volatility: float) -> dict`:
    - Look up `base_pct` from `POSITION_BASE_TABLE[signal]`
    - Look up `conviction_multiplier` by finding the matching range in `CONVICTION_MULTIPLIER_TABLE` for `composite_score`
    - Look up `volatility_adjustment` by finding the matching range in `VOLATILITY_ADJUSTMENT` for `volatility`
    - Compute `final_pct = base_pct * conviction_multiplier * volatility_adjustment`
    - Return `{"base_pct": base_pct, "conviction_multiplier": conviction_multiplier, "volatility_adjustment": volatility_adjustment, "final_pct": final_pct}`
  - [ ] Implement `compute_relative_strength(stock_prices_6m: list[float], nifty_prices_6m: list[float]) -> float`:
    - Compute stock return: `(stock_prices_6m[-1] - stock_prices_6m[0]) / stock_prices_6m[0]`
    - Compute nifty return: `(nifty_prices_6m[-1] - nifty_prices_6m[0]) / nifty_prices_6m[0]`
    - Return `stock_return / nifty_return` (ratio; guard against nifty_return == 0)
  - [ ] Implement `compute_time_stop(price_history: list[float]) -> int`:
    - Starting from the most recent price, scan backwards month by month (approximate: every 21 trading-day entries or daily entries depending on input granularity — document the assumed input unit in a docstring)
    - Count consecutive months where the absolute price change from the prior month's level is less than `MEANINGFUL_MOVEMENT_THRESHOLD`
    - Return the count of such consecutive months (0 if the most recent month shows meaningful movement)
  - [ ] Implement `build_factor_breakdown(factors: dict, roc: float, asymmetry_index: float, time_stop_months: int, position_breakdown: dict) -> dict`:
    - Build the `factors` list: for each key in `FACTOR_WEIGHTS`, construct `{"name": key, "weight": FACTOR_WEIGHTS[key], "raw_value": factors[key], "weighted_contribution": round(factors[key] * FACTOR_WEIGHTS[key], 6), "signal": "positive" if factors[key] >= 0 else "negative"}`
    - Return `{"factors": factors_list, "roc": roc, "asymmetry_index": asymmetry_index, "time_stop_months": time_stop_months, "position_breakdown": position_breakdown}`
    - Output must validate against `FactorBreakdown` Pydantic model without modification

- [ ] Task 3: Create `backend/app/schemas/stock.py` (AC: 9)
  - [ ] Define `FactorItem(BaseModel)` with fields: `name: str`, `weight: float`, `raw_value: float`, `weighted_contribution: float`, `signal: str`
  - [ ] Define `PositionBreakdown(BaseModel)` with fields: `base_pct: float`, `conviction_multiplier: float`, `volatility_adjustment: float`, `final_pct: float`
  - [ ] Define `FactorBreakdown(BaseModel)` with fields: `factors: list[FactorItem]`, `roc: float`, `asymmetry_index: float`, `time_stop_months: int`, `position_breakdown: PositionBreakdown`
  - [ ] Define `StockScoreResponse(BaseModel)` with fields: `id: int`, `stock_symbol: str`, `composite_score: float`, `signal: str`, `position_size: float`, `computation_timestamp: str`, `kite_snapshot_ts: str`, `screener_csv_ts: str`, `rbi_csv_ts: str`, `factor_breakdown: FactorBreakdown`
  - [ ] All string timestamps in ISO 8601 UTC format (`"2026-04-17T10:30:00Z"`); all scores to 4 decimal places; all percentages to 2 decimal places — use Pydantic `Field(decimal_places=...)` or document rounding convention

- [ ] Task 4: Write `backend/app/tests/test_computation_engine.py` (AC: 1, 3, 4, 5, 6, 7, 8, 10)
  - [ ] `test_factor_weights_sum_to_one`: assert `abs(sum(FACTOR_WEIGHTS.values()) - 1.0) < 1e-9`
  - [ ] `test_factor_weights_has_nine_entries`: assert `len(FACTOR_WEIGHTS) == 9`
  - [ ] `test_compute_weighted_score_reference_case`: construct `factors` dict with all 9 keys set to 0.5; compute expected manually as `sum(0.5 * w for w in FACTOR_WEIGHTS.values())`; assert function output matches within `1e-6`. Add a second case with varied per-factor values and document the manual calculation in a comment.
  - [ ] `test_compute_weighted_score_missing_key`: assert `ValueError` raised when a required factor key is absent
  - [ ] `test_compute_roc_reference_case`: call with `[100.0, 105.0, 110.0]`; assert result equals `0.10` within `1e-6` (hand calc: `(110−100)/100 = 0.10`)
  - [ ] `test_compute_roc_empty_raises`: assert `ValueError` on empty list
  - [ ] `test_compute_roc_single_element_raises`: assert `ValueError` on list of length 1
  - [ ] `test_compute_asymmetry_index_reference_case`: call with `(0.3, 0.6, 0.5)`; assert result equals `(-0.3 + 0.6 + 0.5) = 0.8` within `1e-6`
  - [ ] `test_compute_asymmetry_index_all_zeros`: call with `(0.0, 0.0, 0.0)`; assert result equals `0.0`
  - [ ] `test_compute_signal_covers_all_five_states`: parameterised test — for each of the 5 expected signal strings, construct input values that should map to that state per `DECISION_MATRIX`; assert returned string matches
  - [ ] `test_compute_signal_returns_valid_string`: assert all returned signals are members of `{"strong_buy", "buy", "hold", "sell", "strong_sell"}`
  - [ ] `test_compute_position_size_final_pct_formula`: for any valid inputs, assert `result["final_pct"] == result["base_pct"] * result["conviction_multiplier"] * result["volatility_adjustment"]` within `1e-6`
  - [ ] `test_compute_position_size_has_required_keys`: assert returned dict keys == `{"base_pct", "conviction_multiplier", "volatility_adjustment", "final_pct"}`
  - [ ] `test_compute_relative_strength_reference_case`: call with stock `[100.0, 120.0]` and nifty `[100.0, 110.0]`; assert result equals `(0.20 / 0.10) = 2.0` within `1e-6`
  - [ ] `test_compute_relative_strength_nifty_flat_guard`: assert no `ZeroDivisionError` when nifty return is 0 (function returns a guarded fallback, e.g., 1.0 or raises `ValueError` — document the chosen behaviour)
  - [ ] `test_compute_time_stop_zero_when_recent_movement`: call with a price series where the most recent entries show movement ≥ `MEANINGFUL_MOVEMENT_THRESHOLD`; assert result is `0`
  - [ ] `test_build_factor_breakdown_schema_match`: call with all 9 factors set to known values; pass result to `FactorBreakdown(**result)`; assert no `ValidationError`; assert `len(result["factors"]) == 9`
  - [ ] `test_build_factor_breakdown_weighted_contribution`: assert each factor item's `weighted_contribution == raw_value * weight` within `1e-6`
  - [ ] `test_no_io_imports_in_computation_engine`: open `computation_engine.py` source and assert the text does not contain `"kite_client"`, `"database"`, `"models"`, `"requests"`, `"httpx"`, `"sqlmodel"`, `"sqlalchemy"` — grep in pure Python

## Dev Notes

- No prior implementation context — this is the first story in Epic 3; no existing 3.x code to reference.

- **Pure function constraint — ABSOLUTE:** Every function in `computation_engine.py` must be callable in a plain pytest session with no database, no Kite credentials, no environment variables (except what's in `constants.py`). If any function requires a DB session or HTTP client, it is in the wrong file. Move it to `score_service.py`.

- **Factor names:** The architecture document confirms `relative_strength` with weight `0.15` as one of the 9 factors, and names `Valuation`, `Earnings`, `Liquidity` as inputs to the Asymmetry Index. The remaining factors come from the project PRD. The dev agent must look up the PRD or framework documentation to populate all 9 factor names before writing `FACTOR_WEIGHTS`. Do not guess or invent factor names; they must be accurate and consistent with the PRD.

- **Constants isolation — never inline:** Any number that is a framework parameter (weight, threshold, percentage, multiplier) belongs in `constants.py`. A computation function body must not contain numeric literals like `0.65` or `0.15` inline — it reads from the constants only.

- **`compute_time_stop` granularity assumption:** Document in the function docstring whether `price_history` is daily closing prices (use 21-entry segments as monthly proxy) or monthly closing prices (use 1-entry segments). Choose one and document it. The corresponding unit test must use the same granularity.

- **Numeric precision:** Composite scores returned to 4 decimal places — apply `round(value, 4)` at the end of `compute_weighted_score`. Percentages returned to 2 decimal places — apply `round(value, 2)` at the end of `compute_position_size` for `final_pct`, `base_pct`.

- **Anti-patterns to avoid:**
  - Do NOT import `Session` or anything from `sqlmodel`/`sqlalchemy` in `computation_engine.py`
  - Do NOT use `from app.services.kite_client import ...` in `computation_engine.py`
  - Do NOT hardcode weight or threshold values as inline numeric literals inside function bodies
  - Do NOT use `camelCase` for any JSON field in `FactorBreakdown` — all fields are `snake_case` per architecture constraint
  - Do NOT raise `HTTPException` from any computation function — raise `ValueError` or `KeyError` for bad inputs; service layer converts these to domain exceptions

- **`build_factor_breakdown` output — exact JSONB schema required:** The returned dict must match this structure exactly (from `architecture.md#Gap Analysis — Gap 1`):
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
  All 9 factors must appear in the `factors` array (one per FACTOR_WEIGHTS key). Partial `factors` arrays are invalid.

- **`signal` field in each factor item:** Use `"positive"` when `raw_value >= 0`, `"negative"` when `raw_value < 0`. This is the per-factor qualitative signal, distinct from the 5-state portfolio signal.

### Project Structure Notes

Files to **create** (none pre-exist):
- `backend/app/core/constants.py`
- `backend/app/services/computation_engine.py`
- `backend/app/schemas/stock.py`
- `backend/app/tests/test_computation_engine.py`

Files to **leave untouched** (do not modify in this story):
- `backend/app/services/kite_client.py` (Story 3.2)
- `backend/app/services/score_service.py` (Story 3.3)
- `backend/app/api/v1/refresh.py` (Story 3.3)
- `backend/app/core/exceptions.py` (created in Epic 1; add `ComputationError` if not already present)

If `backend/app/core/exceptions.py` does not yet define `ComputationError`, add it in this story — but do not remove any exceptions already defined there.

### References

- [Source: architecture.md#Service Boundaries — computation_engine.py pure functions only]
- [Source: architecture.md#Gap Analysis & Resolutions — Gap 1 (factor_breakdown JSONB schema)]
- [Source: architecture.md#Computation Engine Pattern]
- [Source: architecture.md#Data Architecture — Score Cache & Audit Trail]
- [Source: architecture.md#Naming Patterns — JSON Field Naming Critical Rule (snake_case)]
- [Source: architecture.md#Anti-Patterns (Never Do) — Hardcoded framework weights]
- [Source: epics.md#Epic 3: Computation Engine & Data Refresh — FR20–FR26, NFR15]
- [Source: epics.md#Additional Requirements — factor_breakdown JSONB Schema]

## Dev Agent Record

### Agent Model Used

_to be filled by dev agent_

### Debug Log References

### Completion Notes List

### File List
