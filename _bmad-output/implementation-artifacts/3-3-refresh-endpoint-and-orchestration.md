# Story 3.3: Refresh Endpoint and Orchestration

Status: ready-for-dev

## Story

As an admin user,
I want a `POST /api/v1/refresh` endpoint that pulls all Kite Connect data and recomputes scores for all 50 Nifty 50 stocks in under 3 seconds,
so that the portfolio and analysis screens always reflect current market data with a complete audit trail of which data snapshot was used.

## Acceptance Criteria

1. **Given** an authenticated Viewer user sends `POST /api/v1/refresh`, **When** the server processes the request, **Then** the response is HTTP 403 with error body `{"error": {"code": "FORBIDDEN", "message": "..."}}`.

2. **Given** an authenticated Admin user sends `POST /api/v1/refresh`, **When** the server processes the request using `mock_kite_client` and a test database, **Then** the response is HTTP 200 with body `{"status": "ok", "stocks_computed": 50, "computation_timestamp": "<ISO 8601 UTC string>"}`.

3. **Given** a successful admin refresh with `mock_kite_client`, **When** `SELECT COUNT(*) FROM score_snapshots` is queried after the refresh completes, **Then** the count equals exactly 50 (one row per Nifty 50 stock symbol from `NIFTY_50_SYMBOLS`).

4. **Given** 50 rows exist in `score_snapshots` from a first refresh, **When** a second refresh is triggered by the admin, **Then** `SELECT COUNT(*) FROM score_snapshots` equals 100 — the second refresh appended 50 new rows and did not modify or delete the original 50 rows.

5. **Given** 100 rows exist from two refreshes, **When** `SELECT * FROM score_snapshots WHERE stock_symbol = 'HDFCBANK' ORDER BY computation_timestamp DESC LIMIT 1` is executed, **Then** it returns exactly 1 row whose `computation_timestamp` is from the second refresh (most recent), confirming the latest-per-stock read pattern works correctly.

6. **Given** the 50 rows inserted by a successful refresh are inspected, **When** each row's columns are checked, **Then** every row has non-null values for `factor_breakdown`, `kite_snapshot_ts`, `screener_csv_ts`, and `rbi_csv_ts`.

7. **Given** the `factor_breakdown` JSONB column is read from any inserted row, **When** it is parsed and validated against `FactorBreakdown` Pydantic model, **Then** validation passes without error and `len(factor_breakdown["factors"]) == 9`.

8. **Given** `run_full_refresh` is called and the I/O phase is examined, **When** the function awaits Kite data, **Then** all historical price fetches for the 50 stocks and Nifty index data are launched concurrently using `asyncio.gather` — not sequentially in a loop — so that the 3-second NFR2 target is achievable.

9. **Given** `run_full_refresh` is called and the CPU computation phase is examined, **When** the computation functions are invoked, **Then** they run inside a `ThreadPoolExecutor` via `loop.run_in_executor()` and do not block the asyncio event loop.

10. **Given** any exception occurs during the DB write phase (Phase 3), **When** the exception propagates, **Then** the entire batch INSERT is rolled back (no partial writes), the error is logged at `ERROR` level, and the caller receives `{"error": {"code": "REFRESH_FAILED", "message": "..."}}` with HTTP 500.

## Tasks / Subtasks

- [ ] Task 1: Create `backend/app/services/score_service.py` with `run_full_refresh` (AC: 3, 4, 6, 7, 8, 9, 10)
  - [ ] Define `RefreshResult` dataclass or Pydantic model with fields `stocks_computed: int` and `computation_timestamp: str` (ISO 8601 UTC)
  - [ ] Implement `async def run_full_refresh(session: Session, kite_client: KiteClient) -> RefreshResult`:

    **Phase 1 — I/O (async, concurrent):**
    - Build a list of coroutines: one `asyncio.to_thread(kite_client.get_holdings)`, one `asyncio.to_thread(kite_client.get_nifty_index_prices, 180)`, and 50 coroutines `asyncio.to_thread(kite_client.get_historical_prices, symbol, 180)` — one per symbol in `NIFTY_50_SYMBOLS`
    - Gather all coroutines: `results = await asyncio.gather(*all_coroutines)` — this launches all 52+ I/O operations concurrently
    - Capture `kite_snapshot_ts = datetime.now(UTC)` immediately after `asyncio.gather` returns
    - Unpack results: `holdings`, `nifty_prices_6m`, and a list of per-stock historical prices in the same order as `NIFTY_50_SYMBOLS`

    **Phase 2 — CPU computation (ThreadPoolExecutor):**
    - Fetch per-stock fundamental data from the latest screener CSV batch: `SELECT * FROM screener_data WHERE upload_batch_id = (SELECT MAX(upload_batch_id) FROM screener_data)`
    - Fetch macro data from the latest RBI batch: `SELECT * FROM rbi_macro_data WHERE upload_batch_id = (SELECT MAX(upload_batch_id) FROM rbi_macro_data)`
    - Capture `screener_csv_ts = MAX(uploaded_at) FROM screener_data` and `rbi_csv_ts = MAX(uploaded_at) FROM rbi_macro_data`
    - Create `executor = ThreadPoolExecutor(max_workers=10)` (tune if needed)
    - For each stock in `NIFTY_50_SYMBOLS`, submit computation to executor:
      ```python
      loop = asyncio.get_event_loop()
      futures = [
          loop.run_in_executor(executor, _compute_stock, symbol, stock_prices, nifty_prices_6m, screener_row, rbi_row)
          for symbol, stock_prices, screener_row in zip(NIFTY_50_SYMBOLS, per_stock_prices, screener_rows)
      ]
      computed_results = await asyncio.gather(*futures)
      ```
    - Implement `_compute_stock(symbol, prices_6m, nifty_prices_6m, screener_row, rbi_row) -> dict` as a plain synchronous function (no async) that calls all `computation_engine.*` functions and returns a dict ready for DB insertion

    **Phase 3 — DB write (single transaction):**
    - Open a single DB transaction
    - For each computed result, INSERT one row into `score_snapshots`: `stock_symbol`, `composite_score`, `signal`, `position_size` (final_pct), `computation_timestamp=datetime.now(UTC)`, `kite_snapshot_ts`, `screener_csv_ts`, `rbi_csv_ts`, `factor_breakdown` (JSONB)
    - Commit once all 50 rows are staged — rollback entire transaction on any error
    - Return `RefreshResult(stocks_computed=50, computation_timestamp=computation_timestamp.isoformat() + "Z")`

  - [ ] Implement the `_compute_stock` helper (pure sync, called inside ThreadPoolExecutor):
    - Call `compute_weighted_score(factors)` to get `composite_score`
    - Call `compute_roc(prices_6m[-90:])` to get `roc` (use last 90 entries for 3-month ROC from 6-month history)
    - Call `compute_asymmetry_index(valuation_score, earnings_score, liquidity_score)` from screener data
    - Call `compute_signal(composite_score, roc, asymmetry_index)` to get `signal`
    - Call `compute_position_size(signal, composite_score, volatility)` to get `position_breakdown`
    - Call `compute_relative_strength(prices_6m, nifty_prices_6m)` to get relative strength (used as one of the 9 factors)
    - Call `compute_time_stop(prices_6m)` to get `time_stop_months`
    - Call `build_factor_breakdown(factors, roc, asymmetry_index, time_stop_months, position_breakdown)` to get JSONB payload
    - Return a dict with all fields needed for `score_snapshots` INSERT

- [ ] Task 2: Create `backend/app/api/v1/refresh.py` with `POST /refresh` (AC: 1, 2)
  - [ ] Define the router: `router = APIRouter(prefix="/refresh", tags=["refresh"])`
  - [ ] Implement `POST /` endpoint:
    ```python
    @router.post("/")
    async def trigger_refresh(
        current_user: User = Depends(require_admin),
        session: Session = Depends(get_session)
    ):
    ```
  - [ ] Inside the handler:
    - Instantiate `kite_client = KiteClient(session=session)`
    - Call `result = await score_service.run_full_refresh(session=session, kite_client=kite_client)`
    - Return `{"status": "ok", "stocks_computed": result.stocks_computed, "computation_timestamp": result.computation_timestamp}`
  - [ ] Catch `KiteAPIError` and convert to `HTTPException(status_code=502, detail={"error": {"code": "KITE_API_ERROR", "message": str(e)}})`
  - [ ] Catch any other exception and convert to `HTTPException(status_code=500, detail={"error": {"code": "REFRESH_FAILED", "message": str(e)}})`
  - [ ] Register the router in `backend/app/api/v1/__init__.py` (or wherever the main v1 router is assembled): `api_v1_router.include_router(refresh_router, prefix="/refresh")`

- [ ] Task 3: Write `backend/app/tests/test_api_refresh.py` (AC: 1, 2, 3, 4, 5, 6, 7, 10)
  - [ ] Setup: use `mock_kite_client` fixture from `conftest.py` (Story 3.2); use pytest fixtures for test DB session and auth cookies
  - [ ] `test_viewer_cannot_trigger_refresh`: authenticate as a Viewer user; call `POST /api/v1/refresh`; assert HTTP 403
  - [ ] `test_admin_refresh_returns_200_and_correct_body`: authenticate as Admin; call `POST /api/v1/refresh` with `mock_kite_client` injected; assert HTTP 200; assert response body has `status == "ok"`, `stocks_computed == 50`, and `computation_timestamp` is a parseable ISO 8601 string
  - [ ] `test_refresh_inserts_50_rows`: after one admin refresh, query `SELECT COUNT(*) FROM score_snapshots`; assert count == 50
  - [ ] `test_second_refresh_appends_not_replaces`: run two refreshes; query `SELECT COUNT(*) FROM score_snapshots`; assert count == 100
  - [ ] `test_latest_per_stock_query_returns_most_recent`: after two refreshes, query `SELECT * FROM score_snapshots WHERE stock_symbol = 'HDFCBANK' ORDER BY computation_timestamp DESC LIMIT 1`; assert the returned row's `computation_timestamp` is newer than the first refresh's timestamp
  - [ ] `test_each_row_has_non_null_audit_fields`: after one refresh, load all 50 rows; for each, assert `factor_breakdown IS NOT NULL`, `kite_snapshot_ts IS NOT NULL`, `screener_csv_ts IS NOT NULL`, `rbi_csv_ts IS NOT NULL`
  - [ ] `test_factor_breakdown_schema_valid`: load any row's `factor_breakdown` JSONB; parse with `FactorBreakdown(**row.factor_breakdown)`; assert no `ValidationError`; assert `len(row.factor_breakdown["factors"]) == 9`
  - [ ] `test_refresh_failure_returns_500`: inject a `mock_kite_client` whose `get_holdings()` raises `KiteAPIError`; call `POST /api/v1/refresh`; assert HTTP 500 or 502 with an error body containing `"code"` key

  **Test injection pattern for `mock_kite_client`:**
  Override the `KiteClient` dependency using FastAPI's `app.dependency_overrides` in the test:
  ```python
  def override_kite_client(session=Depends(get_session)):
      return MockKiteClient(session=None)
  app.dependency_overrides[KiteClient] = override_kite_client
  ```
  Or inject via `score_service.run_full_refresh(session, kite_client=mock_kite_client)` if the handler exposes the client as a parameter. Choose one approach and document it in a comment.

## Dev Notes

- No prior implementation context — this is the first story in Epic 3; no existing 3.x code to reference.

- **`score_service.py` is the sole orchestrator:** It is the only module that imports and calls both `kite_client` AND `computation_engine` AND DB. No other module should bridge these three layers. This boundary is explicitly required by `architecture.md#Service Boundaries`.

- **`asyncio.gather` for concurrent I/O — implementation detail:**
  Because `kiteconnect` is a synchronous library, wrap each call with `asyncio.to_thread()` (Python 3.9+) to run it in a thread pool without blocking the event loop. Example:
  ```python
  coros = [asyncio.to_thread(kite_client.get_historical_prices, symbol, 180) for symbol in NIFTY_50_SYMBOLS]
  coros += [asyncio.to_thread(kite_client.get_nifty_index_prices, 180)]
  coros += [asyncio.to_thread(kite_client.get_holdings)]
  all_results = await asyncio.gather(*coros)
  ```
  This launches all 52 I/O operations concurrently. Sequential loops are the main way the 3-second target gets blown — never use `for symbol in symbols: await fetch(symbol)`.

- **CPU phase — ThreadPoolExecutor:** After I/O, the computation is pure Python math. Run each stock's full computation in a thread pool to avoid blocking the event loop:
  ```python
  loop = asyncio.get_running_loop()
  with ThreadPoolExecutor(max_workers=10) as executor:
      futures = [loop.run_in_executor(executor, _compute_stock, ...) for symbol in NIFTY_50_SYMBOLS]
      computed = await asyncio.gather(*futures)
  ```
  Do NOT `await` synchronous computation functions directly — they block. Do NOT use `asyncio.to_thread` for computation (same semantics but `ThreadPoolExecutor` gives explicit concurrency control).

- **`kite_snapshot_ts` source:** The `kiteconnect` API response does not return a server-side timestamp. Use `datetime.now(timezone.utc)` captured immediately after `asyncio.gather` returns for the I/O phase. This is the moment the data was retrieved. Store it as a UTC datetime in the `score_snapshots` table.

- **`screener_csv_ts` and `rbi_csv_ts` query pattern:**
  ```sql
  SELECT MAX(uploaded_at) FROM screener_data WHERE upload_batch_id = (
      SELECT MAX(upload_batch_id) FROM screener_data
  )
  ```
  Run these queries during Phase 2 setup, before entering the executor. Store the results as UTC datetimes. If no CSV data exists yet (table is empty), use `None` and document that the DB column allows NULL for this pre-upload state.

- **`score_snapshots` is APPEND-ONLY:** Never run `UPDATE`, `UPSERT`, or `DELETE` on this table in the refresh path. Every refresh is a clean batch INSERT of 50 new rows. The UI always reads `ORDER BY computation_timestamp DESC LIMIT 1` per stock. An `UPDATE` here is a silent data corruption bug.

- **DB write as single transaction:** Use SQLModel's session context manager:
  ```python
  with session.begin():
      for row_data in computed_results:
          session.add(ScoreSnapshot(**row_data))
  # session.begin() auto-commits on context exit, auto-rolls back on exception
  ```
  Or use explicit `session.commit()` / `session.rollback()`. The key constraint: all 50 INSERTs commit together or none commit.

- **3-month ROC from 6-month price history:** `get_historical_prices(symbol, 180)` returns ~126 trading days. To compute ROC over the last 3 months, use the last ~63 entries: `compute_roc(prices[-63:])`. Document the approximation in `_compute_stock`'s docstring. Do not make a separate `get_historical_prices(symbol, 90)` call — reuse the 6-month data already fetched.

- **Service layer raises domain exceptions, router converts to HTTP:** `score_service.run_full_refresh` must never raise `HTTPException`. It raises `KiteAPIError` (on Kite failures) or `ComputationError` (on engine failures) or propagates DB exceptions. The router in `refresh.py` catches these and converts them to `HTTPException`. This is the mandatory pattern from `architecture.md#Process Patterns — Backend Error Propagation`.

- **Error response shape — must match architecture standard:**
  All error responses use the envelope: `{"error": {"code": "KITE_API_ERROR", "message": "...", "details": {...}}}`. Do not return plain string error messages.

- **Dependency injection for testing:** The `KiteClient` is instantiated inside the route handler (`kite_client = KiteClient(session=session)`). To override it in tests, use FastAPI's `app.dependency_overrides` or refactor the handler to accept `KiteClient` via a `Depends(get_kite_client)` dependency that the test can override. The second approach is cleaner and is recommended — create `def get_kite_client(session=Depends(get_session)) -> KiteClient: return KiteClient(session)` in `dependencies.py`, then override in tests.

- **Anti-patterns to avoid:**
  - Do NOT fetch historical prices with `for symbol in NIFTY_50_SYMBOLS: await kite_client.get_historical_prices(symbol, 180)` — this serialises I/O and makes the 3-second target impossible
  - Do NOT call computation functions with `await` — they are synchronous; awaiting them blocks the event loop without any concurrency benefit
  - Do NOT run `UPDATE score_snapshots SET ...` in the refresh path — append only
  - Do NOT commit DB writes per-stock — one transaction for all 50 rows
  - Do NOT raise `HTTPException` from `score_service.py` — only domain exceptions
  - Do NOT read `screener_data` or `rbi_macro_data` inside `_compute_stock` (it runs in a thread pool separate from the async session context) — read all DB data before entering the executor and pass it as arguments

### Project Structure Notes

Files to **create**:
- `backend/app/services/score_service.py`
- `backend/app/api/v1/refresh.py`
- `backend/app/tests/test_api_refresh.py`

Files to **modify**:
- `backend/app/api/v1/__init__.py` (or equivalent router assembly file) — register the refresh router
- `backend/app/api/v1/dependencies.py` — add `get_kite_client` dependency function (if injection approach is adopted)

Files to **leave untouched** in this story:
- `backend/app/services/computation_engine.py` (Story 3.1 — already complete)
- `backend/app/services/kite_client.py` (Story 3.2 — already complete)
- `backend/app/tests/conftest.py` (Story 3.2 — `mock_kite_client` fixture already defined; only add to it if tests require additional fixtures)

### References

- [Source: architecture.md#Batch Computation Concurrency — asyncio.gather I/O phase + ThreadPoolExecutor CPU phase]
- [Source: architecture.md#Service Boundaries — score_service.py sole orchestrator calling kite_client + computation_engine + DB]
- [Source: architecture.md#Data Flow — Refresh cycle (core value loop)]
- [Source: architecture.md#Data Boundaries — score_snapshots append-on-refresh, latest snapshot per stock]
- [Source: architecture.md#Process Patterns — Backend Error Propagation]
- [Source: architecture.md#API Boundaries — Admin-only: /api/v1/refresh]
- [Source: architecture.md#Format Patterns — API Response Formats (success action, error envelope)]
- [Source: epics.md#Epic 3: Computation Engine & Data Refresh — FR18, FR19, FR27, NFR2, NFR14, NFR15]
- [Source: epics.md#Additional Requirements — asyncio.gather for I/O + ThreadPoolExecutor for CPU, score_snapshots append-only, screener_csv_ts / rbi_csv_ts from latest batch]

## Dev Agent Record

### Agent Model Used

_to be filled by dev agent_

### Debug Log References

### Completion Notes List

### File List
