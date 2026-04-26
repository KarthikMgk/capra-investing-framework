# Story 2.1: CSV Upload Backend

Status: done

## Story

As an admin,
I want to upload Screener.in and RBI macro CSV files through the API with immediate column validation,
so that only structurally correct data reaches the database and invalid uploads are rejected without affecting existing stored data.

## Acceptance Criteria

1. **Given** a valid Screener.in CSV is uploaded to `POST /api/v1/upload/screener`, **When** the request is processed, **Then** all rows are inserted into `screener_data` within a single DB transaction and the response is `HTTP 201` with `{ "status": "ok", "batch_id": "<uuid>" }`.

2. **Given** a valid RBI macro CSV is uploaded to `POST /api/v1/upload/rbi`, **When** the request is processed, **Then** all rows are inserted into `rbi_macro_data` within a single DB transaction and the response is `HTTP 201` with `{ "status": "ok", "batch_id": "<uuid>" }`.

3. **Given** a Screener.in CSV with a missing required column, **When** it is uploaded, **Then** the response is `HTTP 400` with `{ "error": { "code": "CSV_COLUMN_MISSING", "message": "...", "details": { "expected": [...], "found": [...] } } }` and zero rows are written to `screener_data`.

4. **Given** a RBI macro CSV with a missing required column, **When** it is uploaded, **Then** the response is `HTTP 400` with the same error envelope as AC3 and zero rows are written to `rbi_macro_data`.

5. **Given** valid data already exists in `screener_data`, **When** an invalid CSV is uploaded, **Then** the existing rows remain unchanged — the rejection does not touch or truncate existing data.

6. **Given** a viewer (non-admin) submits `POST /api/v1/upload/screener` or `POST /api/v1/upload/rbi`, **When** the request reaches the route handler, **Then** the response is `HTTP 403` — the role check fires before any file processing occurs.

7. **Given** the `csv_validator.py` module, **When** it processes an uploaded file, **Then** it receives the file contents as `bytes` — it never calls `open()`, never writes to disk, and never creates a temporary file.

8. **Given** a second valid Screener.in upload after a first successful one, **When** it is processed, **Then** a new `upload_batch_id` (UUID) is generated and all rows in the second upload share that new batch_id — the first batch's rows remain in the table and are not deleted.

9. **Given** the `screener_data` table is queried for the latest batch, **When** the query uses `WHERE upload_batch_id = (SELECT upload_batch_id FROM screener_data ORDER BY uploaded_at DESC LIMIT 1)`, **Then** it returns only the most recent upload's rows.

10. **Given** `validate_screener()` or `validate_rbi()` is called, **When** column validation completes, **Then** it finishes in under 500ms for files up to 5,000 rows — columns are checked before data types.

## Tasks / Subtasks

- [ ] Task 1: Create the CSV validator service (AC: 3, 4, 7, 10)
  - [ ] Create `backend/app/services/csv_validator.py`
  - [ ] Define `ColumnError(name: str, issue: str)` and `ValidationResult(is_valid: bool, errors: list[ColumnError])` as dataclasses or Pydantic models
  - [ ] Implement `validate_screener(file_bytes: bytes) -> ValidationResult`:
    - Parse bytes in-memory using `pandas.read_csv(io.BytesIO(file_bytes))` — never `open()` or `tempfile`
    - Check columns against `SCREENER_REQUIRED_COLUMNS` (defined as a module-level constant — see Dev Notes for the assumed column list)
    - For each missing column, append a `ColumnError(name=col, issue="missing")`
    - If any errors exist: return `ValidationResult(is_valid=False, errors=errors)` immediately (no type checking)
    - If columns are present: perform basic type checks (e.g. `PE` must be numeric); return `ValidationResult(is_valid=True, errors=[])` on pass
  - [ ] Implement `validate_rbi(file_bytes: bytes) -> ValidationResult`:
    - Same pattern as `validate_screener` but against `RBI_REQUIRED_COLUMNS` constant
    - See Dev Notes for the assumed RBI column list
  - [ ] Both functions must be importable without any FastAPI or DB dependencies — they are pure transformation functions

- [ ] Task 2: Create `CSVValidationError` domain exception (AC: 3, 4)
  - [ ] Open `backend/app/core/exceptions.py` (created in earlier stories or create if absent)
  - [ ] Add `class CSVValidationError(Exception): def __init__(self, errors: list[ColumnError]): self.errors = errors`
  - [ ] This exception is raised from services and caught at the router layer — never raise `HTTPException` from the validator

- [ ] Task 3: Create Pydantic schemas for upload responses (AC: 1, 2, 3)
  - [ ] Create (or modify if partially existing) `backend/app/schemas/upload.py`
  - [ ] Implement `UploadResponse(BaseModel)`: `status: str = "ok"`, `batch_id: str`
  - [ ] Implement `ColumnErrorDetail(BaseModel)`: `expected: list[str]`, `found: list[str]`
  - [ ] Implement `CSVValidationErrorResponse(BaseModel)`: matches the standard error envelope `{ "error": { "code": str, "message": str, "details": ColumnErrorDetail } }`

- [ ] Task 4: Create `screener_data` and `rbi_macro_data` models (AC: 1, 2, 8, 9)
  - [ ] Verify `backend/app/models/screener_data.py` exists (created in Story 1.2 migrations); if not, create it now
  - [ ] `ScreenerData` model columns: `id` (UUID, PK), `upload_batch_id` (UUID, indexed), `uploaded_at` (DateTime, default=now), `symbol` (str), `name` (str), `pe` (float, nullable), `pb` (float, nullable), `eps` (float, nullable), `roe` (float, nullable), `debt_to_equity` (float, nullable), `revenue_growth` (float, nullable), `promoter_holding` (float, nullable)
  - [ ] Verify `backend/app/models/rbi_macro_data.py` exists; if not, create it now
  - [ ] `RbiMacroData` model columns: `id` (UUID, PK), `upload_batch_id` (UUID, indexed), `uploaded_at` (DateTime, default=now), `date` (Date), `repo_rate` (float), `credit_growth` (float), `liquidity_indicator` (float)
  - [ ] If either model is new, generate and apply an Alembic migration

- [ ] Task 5: Implement the upload API router (AC: 1, 2, 3, 4, 5, 6, 7, 8)
  - [ ] Create `backend/app/api/v1/upload.py`
  - [ ] Implement `POST /api/v1/upload/screener`:
    - Depends on `require_admin`
    - Accept `file: UploadFile` (FastAPI multipart)
    - Read file contents: `file_bytes = await file.read()` — this gives `bytes`, no disk write
    - Call `validate_screener(file_bytes)` — if `not result.is_valid`: raise `CSVValidationError(result.errors)`, which the router catches and converts to HTTP 400 with error envelope; zero DB writes happen in this branch
    - If valid: generate `batch_id = str(uuid.uuid4())`; parse CSV in-memory; open a DB session; INSERT all rows in a single transaction; commit; return `UploadResponse(status="ok", batch_id=batch_id)` with HTTP 201
  - [ ] Implement `POST /api/v1/upload/rbi`: same pattern, uses `validate_rbi()` and inserts into `rbi_macro_data`
  - [ ] Add an exception handler for `CSVValidationError` at the router level (or register in `main.py`) that returns the standard 400 error envelope
  - [ ] Register the upload router in `backend/app/api/v1/__init__.py` with prefix `/api/v1/upload`

- [ ] Task 6: Write CSV validator tests (AC: 3, 4, 7, 10)
  - [ ] Create `backend/app/tests/test_csv_validator.py`
  - [ ] Test `validate_screener`: valid CSV with all required columns → `is_valid=True`
  - [ ] Test `validate_screener`: CSV missing column `PE` → `is_valid=False`, errors list contains an error mentioning `PE`
  - [ ] Test `validate_screener`: CSV with correct columns but wrong type in `PE` column → `is_valid=False`, errors mention type mismatch
  - [ ] Test `validate_screener`: empty file (zero bytes) → `is_valid=False`
  - [ ] Test `validate_rbi`: valid RBI CSV → `is_valid=True`
  - [ ] Test `validate_rbi`: CSV missing `Repo_Rate` column → `is_valid=False`
  - [ ] All tests pass `bytes` directly to the validator — no file paths, no `open()` calls in test code
  - [ ] Performance benchmark test (AC: 10): generate a 5,000-row valid Screener CSV in-memory using `io.StringIO` + `pandas`, time the `validate_screener()` call, assert `elapsed_seconds < 0.5` using `time.perf_counter()` — this verifies NFR3 at the service layer

- [ ] Task 7: Write upload API endpoint tests (AC: 1, 2, 5, 6, 8, 9)
  - [ ] Create `backend/app/tests/test_api_upload.py`
  - [ ] Test viewer upload returns HTTP 403 (both endpoints)
  - [ ] Test invalid Screener CSV returns HTTP 400 with `error.code == "CSV_COLUMN_MISSING"` and `error.details.expected` and `error.details.found` populated
  - [ ] Test valid Screener CSV returns HTTP 201 with `batch_id` UUID in response
  - [ ] Test that after a failed upload, existing `screener_data` rows are unchanged (seed one valid batch first, then attempt invalid upload, then assert count unchanged)
  - [ ] Test second valid upload creates a new `batch_id` and both batches exist in DB; verify `WHERE upload_batch_id = (SELECT upload_batch_id FROM screener_data ORDER BY uploaded_at DESC LIMIT 1)` returns only the second batch

## Dev Notes

- No prior implementation context — this is an early story in the sprint. Stories 1.1 (scaffold), 1.2 (Alembic migrations), and 1.3 (auth backend with `require_admin`) must be complete. The `screener_data` and `rbi_macro_data` tables may have been partially defined in Story 1.2 — verify before creating new model files.

- **CSV files MUST be processed as `bytes` — never written to disk.** This is NFR10. The correct pattern is:
  ```python
  file_bytes = await file.read()  # bytes — no disk I/O
  result = validate_screener(file_bytes)  # pass bytes to validator
  # inside validator:
  import io, pandas as pd
  df = pd.read_csv(io.BytesIO(file_bytes))  # in-memory only
  ```
  Anti-pattern: `with open(tmpfile, "wb") as f: f.write(...)` — NEVER do this.

- **Assumed Screener.in column schema (document as assumptions):** The architecture and PRD do not provide an exact canonical Screener.in column list. The following are the assumed required columns based on the PRD's described framework factors. The dev must verify these against a real Screener.in export and update the constant if needed:
  ```python
  SCREENER_REQUIRED_COLUMNS = [
      "Symbol", "Name", "PE", "PB", "EPS",
      "ROE", "Debt_to_Equity", "Revenue_Growth", "Promoter_Holding"
  ]
  ```
  This assumption list should be verified against an actual Screener.in CSV export before final implementation. Column names are case-sensitive in the validator — if Screener.in exports lowercase names (e.g. `pe` instead of `PE`), update the constant accordingly. Document the verified list in the task completion notes.

- **Assumed RBI macro column schema (document as assumptions):** Similarly assumed from PRD description:
  ```python
  RBI_REQUIRED_COLUMNS = ["Date", "Repo_Rate", "Credit_Growth", "Liquidity_Indicator"]
  ```
  Verify against a real RBI macro data export before finalizing.

- **`upload_batch_id` behavior:** Every upload generates a fresh UUID4. All rows in one upload share the same `upload_batch_id`. Old batches are NOT deleted — they remain in the table. The computation engine reads the latest batch using:
  ```sql
  WHERE upload_batch_id = (
    SELECT upload_batch_id FROM screener_data ORDER BY uploaded_at DESC LIMIT 1
  )
  ```
  This "append and read latest" pattern is intentional for auditability.

- **Transaction scope:** All DB inserts for a single upload must be inside one transaction. If any row insert fails, the entire transaction rolls back. Use SQLAlchemy session context manager:
  ```python
  async with session.begin():
      session.add_all(rows)
  # commits on exit; rolls back on exception
  ```

- **Error response shape — exact format required:**
  ```json
  {
    "error": {
      "code": "CSV_COLUMN_MISSING",
      "message": "Required columns are missing from the uploaded CSV.",
      "details": {
        "expected": ["Symbol", "PE", "PB"],
        "found": ["symbol", "pe", "pb"]
      }
    }
  }
  ```
  The `details.found` list should contain the actual column names from the uploaded file.

- **`require_admin` dependency:** Import from `backend/app/api/v1/dependencies.py`. Both upload endpoints must use `Depends(require_admin)`. The role check fires before file reading — a 403 must not involve reading the multipart body.

- **pandas is a dependency:** Add `pandas` to `backend/requirements.txt` if not already present. It is used for in-memory CSV parsing only.

- **File paths — exact list to create or modify:**
  - `backend/app/services/csv_validator.py` (new)
  - `backend/app/core/exceptions.py` (modify — add `CSVValidationError`)
  - `backend/app/schemas/upload.py` (new or modify)
  - `backend/app/models/screener_data.py` (new or verify existing)
  - `backend/app/models/rbi_macro_data.py` (new or verify existing)
  - `backend/app/api/v1/upload.py` (new)
  - `backend/app/api/v1/__init__.py` (modify — register upload router)
  - `backend/app/tests/test_csv_validator.py` (new)
  - `backend/app/tests/test_api_upload.py` (new)
  - `backend/alembic/versions/<timestamp>_*.py` (auto-generated if new models)

### Project Structure Notes

- `csv_validator.py` lives in `services/` — it is a service, not a utility. It accepts `bytes` and returns a domain result object.
- `exceptions.py` lives in `core/` — domain exceptions are cross-cutting concerns.
- Test files live at `backend/app/tests/` — never co-located with source files.
- The validator module must have zero FastAPI imports — it must be testable without an HTTP context.
- Column name constants (`SCREENER_REQUIRED_COLUMNS`, `RBI_REQUIRED_COLUMNS`) live as module-level constants in `csv_validator.py` — not in `core/constants.py` since they are specific to validation logic.

### References

- [Source: architecture.md#Data Architecture — CSV Data Storage]
- [Source: architecture.md#API & Communication Patterns — Error Response Shape]
- [Source: architecture.md#Project Structure & Boundaries — Backend Project Organization, Service Boundaries, Data Boundaries]
- [Source: architecture.md#Implementation Patterns & Consistency Rules — CSV Validation Pattern, Process Patterns]
- [Source: architecture.md#Implementation Patterns & Consistency Rules — Anti-Patterns (open() for CSV validation)]
- [Source: architecture.md#Data Flow — CSV upload (data ingestion loop)]
- [Source: epics.md#Epic 2: CSV Data Upload]
- [Source: epics.md#FR28, FR29, FR30, FR31, FR32, FR33, FR34, FR40]
- [Source: epics.md#Additional Requirements — Memory-only CSV validation, CSV Batch IDs]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6 (1M context)

### Completion Notes List

- Router placed in `api/routes/upload.py` (not `api/v1/`) — matches project structure
- Tests in `tests/` (not `app/tests/`) — matches project structure
- `ScreenerData` model updated: old Story 1.2 columns (stock_symbol, pe_ratio, etc.) replaced with spec columns (symbol, name, pe, pb, revenue_growth, promoter_holding). Migration `c4d5e6f7a8b9` handles the transition.
- `RBIMacroData` model updated: `date` column added (DateType alias used to avoid name collision with field named `date`)
- `test_db_schema.py` updated to verify new column names
- `CSVValidationError` already existed with compatible `(message, details)` signature — used as-is, no change needed
- Validator is pure bytes→ValidationResult with no FastAPI/DB imports; passes all AC10 perf tests (<500ms for 5000 rows)
- `pandas>=2.0` added to `pyproject.toml`

### File List

- `backend/app/services/__init__.py` (new)
- `backend/app/services/csv_validator.py` (new)
- `backend/app/models/screener_data.py` (modified — new column schema)
- `backend/app/models/rbi_macro_data.py` (modified — added date column)
- `backend/app/alembic/versions/c4d5e6f7a8b9_update_screener_rbi_schema.py` (new)
- `backend/app/schemas/upload.py` (new)
- `backend/app/api/routes/upload.py` (new)
- `backend/app/api/main.py` (modified — registered upload router)
- `backend/app/main.py` (modified — added CSVValidationError handler)
- `backend/pyproject.toml` (modified — added pandas)
- `backend/tests/test_db_schema.py` (modified — updated column assertions)
- `backend/tests/test_csv_validator.py` (new — 9 tests)
- `backend/tests/test_api_upload.py` (new — 9 tests)
