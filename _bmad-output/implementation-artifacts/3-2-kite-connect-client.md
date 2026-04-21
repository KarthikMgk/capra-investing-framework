# Story 3.2: Kite Connect Client

Status: ready-for-dev

## Story

As a developer,
I want a `KiteClient` wrapper around the official `kiteconnect` Python library that validates every API response before returning data,
so that malformed Kite data never silently reaches the computation engine and tests can substitute a mock client without live credentials.

## Acceptance Criteria

1. **Given** `backend/app/services/kite_client.py` exists, **When** the file is statically scanned for raw HTTP calls (`requests.get`, `httpx`, `urllib`, `http.client`), **Then** zero matches are found — all Kite communication is routed through the `kiteconnect` library exclusively.

2. **Given** `KiteClient` is instantiated with a valid `session` containing encrypted Kite credentials, **When** `__init__` completes, **Then** a `KiteConnect` object is created with the decrypted API key and the access token is set via `kite.set_access_token(access_token)`.

3. **Given** `get_holdings()` is called and the Kite API returns a response where any holding item is missing a required field (`tradingsymbol`, `quantity`, or `last_price`), **When** the schema validation runs, **Then** `KiteAPIError` is raised and no `HoldingData` objects are returned.

4. **Given** `get_holdings()` is called and the Kite API returns a well-formed response, **When** the method returns, **Then** the result is `list[HoldingData]` with `tradingsymbol`, `quantity`, and `last_price` populated on every item.

5. **Given** `get_historical_prices(symbol, days=90)` is called, **When** the method returns, **Then** the result is a `list[float]` of closing prices with length approximately equal to the number of trading days in `days` calendar days (at minimum 1 element), and no element is `None` or non-numeric.

6. **Given** `get_historical_prices(symbol, days=180)` is called for a Nifty 50 symbol, **When** the method returns, **Then** the result contains 6 months of daily closing prices suitable as direct input to `compute_relative_strength()` in Story 3.1.

7. **Given** any Kite Connect network error or authentication error occurs inside any `KiteClient` method, **When** the exception propagates, **Then** it is caught, logged at `ERROR` level using the Python `logging` module, and re-raised as `KiteAPIError` — the raw `kiteconnect` exception never reaches the caller.

8. **Given** the pytest fixture `mock_kite_client` is imported from `backend/app/tests/conftest.py`, **When** a test uses it in place of a real `KiteClient`, **Then** the fixture returns an object whose `get_holdings()`, `get_quote()`, `get_historical_prices()`, and `get_nifty_index_prices()` methods return predictable, hard-coded responses of the correct type — no live API call is made.

9. **Given** `backend/app/schemas/portfolio.py` exists, **When** `HoldingData`, `QuoteData`, `PortfolioResponse`, and `HoldingWithSignal` are imported and instantiated with valid data, **Then** Pydantic accepts them without raising `ValidationError`.

## Tasks / Subtasks

- [ ] Task 1: Create `backend/app/services/kite_client.py` with the `KiteClient` class (AC: 1, 2, 3, 4, 5, 6, 7)
  - [ ] Add `kiteconnect` to `backend/requirements.txt` (PyPI package name: `kiteconnect`; confirm latest stable version and pin it)
  - [ ] Implement `KiteClient.__init__(self, session: Session)`:
    - Query the DB `session` for the stored Kite credentials row
    - Call `encryption.decrypt(encrypted_api_key)` and `encryption.decrypt(encrypted_access_token)` from `app.core.encryption`
    - Instantiate `self.kite = KiteConnect(api_key=decrypted_api_key)`
    - Call `self.kite.set_access_token(decrypted_access_token)`
    - Log at `INFO` level: `"KiteClient initialised for API key ending in ...{last_4_chars}"`
  - [ ] Implement `get_holdings(self) -> list[HoldingData]`:
    - Call `raw = self.kite.holdings()`
    - For each item in `raw`, validate presence of `tradingsymbol`, `quantity`, `last_price` using a helper `_validate_holding_item(item)` — raises `KiteAPIError` on missing keys
    - Construct and return `[HoldingData(tradingsymbol=..., quantity=..., last_price=...) for item in raw]`
    - Wrap all kiteconnect calls in `try/except Exception as e: logger.error(...); raise KiteAPIError(...) from e`
  - [ ] Implement `get_quote(self, symbols: list[str]) -> dict[str, QuoteData]`:
    - Call `raw = self.kite.quote(symbols)` (kiteconnect expects symbols like `["NSE:HDFCBANK", "NSE:RELIANCE"]`)
    - For each symbol key in `raw`, validate presence of `last_price`; validate `change` and `change_percent` if available (treat as 0.0 if absent)
    - Return `{symbol: QuoteData(last_price=..., change=..., change_percent=...) for symbol, data in raw.items()}`
    - On any schema mismatch or network error, raise `KiteAPIError`
  - [ ] Implement `get_historical_prices(self, symbol: str, days: int) -> list[float]`:
    - Determine `to_date = datetime.now(UTC).date()` and `from_date = to_date - timedelta(days=days)`
    - Resolve the instrument token for `symbol` using `self.kite.instruments("NSE")` or a cached lookup (instrument token is required by kiteconnect `historical_data()`)
    - Call `raw = self.kite.historical_data(instrument_token, from_date, to_date, "day")` — interval `"day"` for daily OHLCV
    - Validate that `raw` is a non-empty list and each item contains a `"close"` key
    - Return `[float(candle["close"]) for candle in raw]`
    - On any error, raise `KiteAPIError`
  - [ ] Implement `get_nifty_index_prices(self, days: int) -> list[float]`:
    - Use NSE Nifty 50 index instrument. In kiteconnect, the Nifty 50 index is accessed via instrument `"NSE:NIFTY 50"` for quotes; for historical data, use the index instrument token (look up in `kite.instruments("NSE")` where `tradingsymbol == "NIFTY 50"` and `instrument_type == "INDEX"`)
    - Call `get_historical_prices` logic adapted for this instrument token
    - Return list of daily closing values for the Nifty 50 index
    - On any error, raise `KiteAPIError`
  - [ ] Add module-level logger: `logger = logging.getLogger(__name__)`
  - [ ] Instrument token caching: to avoid calling `kite.instruments()` on every historical price request, cache the Nifty 50 instruments list as a class-level or module-level dict after the first call

- [ ] Task 2: Create `backend/app/schemas/portfolio.py` (AC: 9)
  - [ ] Define `HoldingData(BaseModel)` with fields: `tradingsymbol: str`, `quantity: float`, `last_price: float`
  - [ ] Define `QuoteData(BaseModel)` with fields: `last_price: float`, `change: float = 0.0`, `change_percent: float = 0.0`
  - [ ] Define `HoldingWithSignal(BaseModel)` with fields: `tradingsymbol: str`, `name: str`, `quantity: float`, `last_price: float`, `signal: str`, `signal_color: str`
  - [ ] Define `PortfolioResponse(BaseModel)` with fields: `items: list[HoldingWithSignal]`, `total: int`
  - [ ] All field names in `snake_case` — never `camelCase` — per architecture constraint

- [ ] Task 3: Extend `backend/app/tests/conftest.py` with the `mock_kite_client` fixture (AC: 8)
  - [ ] If `conftest.py` does not exist, create it; if it exists (from Epic 1/2), add the fixture without removing existing fixtures
  - [ ] Define `class MockKiteClient` inheriting from `KiteClient` with `__init__` overridden to NOT call the DB or decrypt credentials (accept a `session` parameter but ignore it)
  - [ ] Override `get_holdings()` to return a hard-coded `list[HoldingData]` with 3–5 realistic Nifty 50 symbols
  - [ ] Override `get_quote(symbols)` to return a hard-coded `dict[str, QuoteData]` for the symbols in the mock holdings
  - [ ] Override `get_historical_prices(symbol, days)` to return a deterministic list of 90 floats (for `days=90`) or 180 floats (for `days=180`) — use a simple synthetic price series (e.g., 100.0 + 0.1 × i for i in range(days)) so the series is predictable and tests can compute expected values
  - [ ] Override `get_nifty_index_prices(days)` to return a deterministic list of `days` floats representing a flat or slightly rising Nifty index
  - [ ] Add pytest fixture:
    ```python
    @pytest.fixture
    def mock_kite_client():
        return MockKiteClient(session=None)
    ```

- [ ] Task 4: Write unit tests using `mock_kite_client` fixture (AC: 3, 4, 5, 7, 8)
  - [ ] `test_get_holdings_returns_list_of_holding_data`: assert `isinstance(result, list)` and `isinstance(result[0], HoldingData)` using `mock_kite_client`
  - [ ] `test_get_holdings_schema_validation_raises_kite_api_error`: create a `MockKiteClient` subclass where `kite.holdings()` returns `[{"tradingsymbol": "HDFCBANK"}]` (missing `quantity` and `last_price`); assert `KiteAPIError` is raised
  - [ ] `test_get_historical_prices_returns_floats`: call `mock_kite_client.get_historical_prices("HDFCBANK", 90)`; assert all items are `float` and list length is 90
  - [ ] `test_get_historical_prices_6m_length`: call with `days=180`; assert list length is 180
  - [ ] `test_kite_api_error_wraps_kiteconnect_exceptions`: create a `MockKiteClient` that raises a native `kiteconnect.exceptions.NetworkException` from `get_holdings()`; assert the test sees `KiteAPIError` (not the raw kiteconnect exception)
  - [ ] Mark all tests that require real Kite credentials with `@pytest.mark.integration` — these are skipped in CI by default (`pytest -m "not integration"`)

## Dev Notes

- No prior implementation context — this is the first story in Epic 3; no existing 3.x code to reference.

- **Official library only:** Install via `pip install kiteconnect`. Never call Zerodha's REST API directly with `requests`, `httpx`, or `urllib`. The `kiteconnect` library wraps all endpoints. This is a hard requirement from NFR13.

- **`KiteAPIError` location:** This exception must be defined in `backend/app/core/exceptions.py` (created in Epic 1). If not yet defined there, add it in this story. The class should carry a `message: str` and optionally a `code: str` field. Do not define it inside `kite_client.py`.

- **Constructor injection pattern — mandatory:** `KiteClient(session: Session)` receives its DB session from the outside. Tests construct `MockKiteClient(session=None)`. The FastAPI dependency layer (Story 3.3) will pass a real `Session` from `Depends(get_session)`. This decoupling is the mechanism that satisfies NFR15.

- **Instrument token lookup for historical data:** The `kiteconnect` `historical_data()` method requires an integer instrument token, not the ticker symbol string. The instruments list (`kite.instruments("NSE")`) can have hundreds of entries. Implement a helper `_get_instrument_token(self, symbol: str) -> int` that filters the instruments list for the matching `tradingsymbol`. Cache this mapping (dict) at class level after the first retrieval to avoid repeated API calls within a single refresh cycle.

- **Historical price call signature (kiteconnect library):**
  ```python
  kite.historical_data(
      instrument_token=token,
      from_date=from_date,   # datetime.date object
      to_date=to_date,       # datetime.date object
      interval="day"         # daily OHLCV candles
  )
  ```
  Returns a list of dicts; each dict has keys: `date`, `open`, `high`, `low`, `close`, `volume`.

- **`get_historical_prices` days mapping:**
  - 3-month ROC input: `get_historical_prices(symbol, days=90)` — returns ~63 trading-day closing prices
  - 6-month relative strength input: `get_historical_prices(symbol, days=180)` — returns ~126 trading-day closing prices
  - The list length will be trading days in the calendar span (not calendar days) — computation functions must be robust to variable list lengths.

- **`get_nifty_index_prices` instrument:** The Nifty 50 index instrument token can be found by filtering `kite.instruments("NSE")` where `tradingsymbol == "NIFTY 50"` and `segment == "INDICES"`. Confirm with the live kiteconnect docs; the token value changes — do not hardcode it.

- **Error logging pattern — always follow this sequence:**
  ```python
  except Exception as e:
      logger.error("KiteClient.get_holdings failed: %s", str(e), exc_info=True)
      raise KiteAPIError(f"Failed to fetch holdings: {e}") from e
  ```
  The `exc_info=True` preserves the original traceback in logs. Always use `raise ... from e` to chain exceptions. Never `raise KiteAPIError(...)` without `from e`.

- **Schema validation helper pattern:**
  ```python
  def _validate_holding_item(self, item: dict) -> None:
      required = {"tradingsymbol", "quantity", "last_price"}
      missing = required - item.keys()
      if missing:
          raise KiteAPIError(f"Holding response missing fields: {missing}")
  ```
  Call this before constructing `HoldingData`. Do the same for `QuoteData`. Never silently ignore missing fields.

- **`mock_kite_client` synthetic price series — determinism requirement:** The mock must produce the same list on every call so that tests can pre-compute expected values and assert exact results. Using `[100.0 + 0.1 * i for i in range(days)]` achieves this. The series should show meaningful variation (not all-flat) so Time Stop and ROC tests are non-trivial.

- **Anti-patterns to avoid:**
  - Do NOT call `kite.historical_data()` with a symbol string — it requires an integer instrument token
  - Do NOT cache credentials as module-level globals — they are per-session and must be decrypted on `__init__`
  - Do NOT suppress exceptions silently — every caught exception must be logged and re-raised as `KiteAPIError`
  - Do NOT import `kiteconnect` inside `computation_engine.py` — ever
  - Do NOT write a `KiteClient` that cannot be subclassed for mocking (avoid `@staticmethod` or `@classmethod` on data-fetching methods)
  - Do NOT use `camelCase` in `schemas/portfolio.py` field names

### Project Structure Notes

Files to **create**:
- `backend/app/services/kite_client.py`
- `backend/app/schemas/portfolio.py`

Files to **modify**:
- `backend/requirements.txt` — add `kiteconnect` with pinned version
- `backend/app/tests/conftest.py` — add `mock_kite_client` fixture (create file if not present)
- `backend/app/core/exceptions.py` — add `KiteAPIError` class if not already defined

Files to **leave untouched** in this story:
- `backend/app/services/computation_engine.py` (Story 3.1)
- `backend/app/services/score_service.py` (Story 3.3)
- `backend/app/api/v1/refresh.py` (Story 3.3)

### References

- [Source: architecture.md#Service Boundaries — kite_client.py all Kite Connect I/O; validates response schema before returning]
- [Source: architecture.md#Authentication & Security — Kite Connect Credential Storage (AES-256 decrypt on init)]
- [Source: architecture.md#Process Patterns — Backend Error Propagation (domain exceptions, ERROR log level)]
- [Source: architecture.md#Batch Computation Concurrency — async gather I/O phase → thread pool CPU phase]
- [Source: epics.md#Epic 3: Computation Engine & Data Refresh — NFR13, NFR14, NFR15]
- [Source: epics.md#Additional Requirements — asyncio.gather for I/O phase]

## Dev Agent Record

### Agent Model Used

_to be filled by dev agent_

### Debug Log References

### Completion Notes List

### File List
