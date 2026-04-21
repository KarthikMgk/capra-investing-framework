# Story 1.5: Kite Credential Storage

Status: ready-for-dev

## Story

As an admin,
I want to securely enter and store my Kite Connect API key and access token via a settings screen,
so that the system can authenticate with Kite Connect on my behalf without ever exposing my credentials in plaintext.

## Acceptance Criteria

1. **Given** the encryption module exists, **When** `encrypt(plaintext)` is called, **Then** it returns a ciphertext string that is NOT equal to the input — and `decrypt(ciphertext)` returns the original plaintext.

2. **Given** the encryption uses AES-256-GCM (not Fernet), **When** `encryption.py` is inspected, **Then** it imports from `cryptography.hazmat.primitives.ciphers.aead.AESGCM` and the key is exactly 32 bytes — satisfying NFR7's AES-256 requirement.

3. **Given** `ENCRYPTION_KEY` is not set in the environment, **When** the backend starts, **Then** it raises a startup error (via pydantic-settings validation) — the app never runs without an encryption key.

4. **Given** an admin is authenticated, **When** they send `PUT /api/v1/settings/kite` with `{ "api_key": "...", "access_token": "..." }`, **Then** both values are encrypted before being written to the database — the stored column values are ciphertext, not plaintext.

5. **Given** credentials are stored, **When** an admin sends `GET /api/v1/settings/kite`, **Then** the response contains `{ "api_key_set": true, "access_token_set": true, "updated_at": "..." }` — no plaintext credential value is ever returned.

6. **Given** a viewer (non-admin) is authenticated, **When** they send `GET /api/v1/settings/kite` or `PUT /api/v1/settings/kite`, **Then** the response is 403 — the role guard fires before any credential logic runs.

7. **Given** the `kite_settings` table exists, **When** a PUT is issued for the first time, **Then** a row is created (INSERT). When a PUT is issued again, **Then** the existing row is updated (UPSERT) — no duplicate rows accumulate.

8. **Given** the `/admin/settings` route in the frontend, **When** an admin navigates to it, **Then** they see a form with two password-type inputs (API key, access token) and masked status indicators showing whether each credential is currently set.

9. **Given** the admin submits the settings form with valid values, **When** the PUT request succeeds, **Then** a success message is shown inline and the status indicators update to reflect that credentials are now set.

10. **Given** the backend tests run, **When** the PUT test is executed, **Then** it asserts that the value stored in the database is NOT equal to the submitted plaintext — confirming encryption happened.

## Tasks / Subtasks

- [ ] Task 1: Implement AES-256-GCM encryption utilities (AC: 1, 2, 3)
  - [ ] Create `backend/app/core/encryption.py`
  - [ ] Import `AESGCM` from `cryptography.hazmat.primitives.ciphers.aead` — do NOT use Fernet (Fernet is AES-128-CBC, which does not satisfy NFR7's AES-256 requirement)
  - [ ] Implement `encrypt(plaintext: str) -> str`: generate a random 12-byte nonce, encrypt with AESGCM using the key from `settings.ENCRYPTION_KEY`, return `base64(nonce + ciphertext)` as a URL-safe base64 string
  - [ ] Implement `decrypt(ciphertext: str) -> str`: decode base64, split nonce (first 12 bytes) from ciphertext, decrypt with AESGCM, return plaintext string
  - [ ] Key loading: call `settings.ENCRYPTION_KEY` which must be a 32-byte key encoded as URL-safe base64 (configured in `core/config.py` via pydantic-settings); raise `ValueError` if the decoded key is not exactly 32 bytes
  - [ ] Add `ENCRYPTION_KEY` to `backend/app/core/config.py` `Settings` class as a required field (no default); pydantic-settings will raise `ValidationError` on startup if absent

- [ ] Task 2: Create `kite_settings` database model and Alembic migration (AC: 4, 7)
  - [ ] Create `backend/app/models/kite_settings.py`: SQLModel table `KiteSettings` with columns: `id` (UUID, primary key), `api_key_encrypted` (Text), `access_token_encrypted` (Text), `updated_at` (DateTime, auto-updated)
  - [ ] Run `alembic revision --autogenerate -m "add kite_settings table"` to generate a migration file
  - [ ] Verify the migration file in `backend/alembic/versions/` contains the correct `CREATE TABLE kite_settings` DDL
  - [ ] Apply the migration to confirm it runs without error: `alembic upgrade head`

- [ ] Task 3: Create Pydantic schemas for the settings API (AC: 4, 5)
  - [ ] Create `backend/app/schemas/settings.py`
  - [ ] Implement `KiteCredentialsUpdate(BaseModel)`: `api_key: str`, `access_token: str` — both required, no Optional
  - [ ] Implement `KiteCredentialsStatus(BaseModel)`: `api_key_set: bool`, `access_token_set: bool`, `updated_at: datetime | None`

- [ ] Task 4: Implement the settings API router (AC: 4, 5, 6, 7)
  - [ ] Create `backend/app/api/v1/settings.py`
  - [ ] Implement `GET /api/v1/settings/kite`: depends on `require_admin`; queries the `kite_settings` table; returns `KiteCredentialsStatus` — `api_key_set: bool(row.api_key_encrypted is not None)`, `access_token_set: bool(...)`, `updated_at: row.updated_at`; returns `{"api_key_set": false, "access_token_set": false, "updated_at": null}` if no row exists
  - [ ] Implement `PUT /api/v1/settings/kite`: depends on `require_admin`; accepts `KiteCredentialsUpdate`; calls `encrypt()` on both fields; performs upsert into `kite_settings` (INSERT if no row, UPDATE if row exists — use a single-row table pattern: SELECT, then INSERT or UPDATE); returns `{"status": "ok"}`
  - [ ] Register the settings router in `backend/app/api/v1/__init__.py` (or wherever the v1 router is assembled); confirm the prefix is `/api/v1/settings`
  - [ ] Never log the plaintext api_key or access_token — log only `"kite credentials updated"` at INFO level on successful PUT

- [ ] Task 5: Create the AdminSettings frontend screen (AC: 8, 9)
  - [ ] Create `frontend/src/features/admin/AdminSettings.tsx`
  - [ ] On mount: call `GET /api/v1/settings/kite` (via TanStack Query `useQuery`) and display status indicators — "API Key: SET" / "API Key: NOT SET" per `api_key_set` boolean
  - [ ] Render a form with two `<input type="password">` fields: API Key and Access Token
  - [ ] On submit: call `PUT /api/v1/settings/kite` via `useMutation`; on success show inline success message and refetch status query; on error show inline error message
  - [ ] Both inputs use `type="password"` — values are masked and never shown in plaintext in the UI
  - [ ] Create `frontend/src/features/admin/useAdminSettings.ts` (optional extraction of the TanStack hooks if the component grows unwieldy)

- [ ] Task 6: Wire AdminSettings into App.tsx under `/admin/settings` (AC: 8)
  - [ ] Open `frontend/src/App.tsx` (existing file — add route alongside existing routes, do not recreate)
  - [ ] Add `/admin/settings` as a child route wrapped in `<AdminRoute>` (already implemented in Story 1.4)
  - [ ] Import `AdminSettings` and use it as the route element

- [ ] Task 7: Write backend tests (AC: 4, 5, 6, 10)
  - [ ] Create (or add to) `backend/app/tests/test_api_settings.py`
  - [ ] Test `PUT /api/v1/settings/kite` as admin: assert HTTP 200; query the DB and assert `api_key_encrypted != submitted_api_key` (encrypted value differs from plaintext)
  - [ ] Test `GET /api/v1/settings/kite` as admin after PUT: assert `api_key_set == true`, `access_token_set == true`, and neither field in the response equals the plaintext values
  - [ ] Test `GET /api/v1/settings/kite` as viewer: assert HTTP 403
  - [ ] Test `PUT /api/v1/settings/kite` as viewer: assert HTTP 403
  - [ ] Test second PUT (upsert): assert that a second PUT does not create a second row — `SELECT COUNT(*) FROM kite_settings` still equals 1

## Dev Notes

- No prior implementation context — this is an early story in the sprint. Stories 1.1 (scaffold), 1.2 (Alembic migrations for other tables), and 1.3 (auth backend with `require_admin`) must be complete first. This story adds one new table to the schema.

- **AES-256-GCM is required — Fernet is not acceptable.** Fernet uses AES-128-CBC internally. NFR7 explicitly mandates AES-256. Use `cryptography.hazmat.primitives.ciphers.aead.AESGCM` with a 32-byte key. Example:
  ```python
  import os, base64
  from cryptography.hazmat.primitives.ciphers.aead import AESGCM

  def encrypt(plaintext: str, key: bytes) -> str:
      aesgcm = AESGCM(key)  # key must be 32 bytes for AES-256
      nonce = os.urandom(12)  # 96-bit nonce for GCM
      ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
      return base64.urlsafe_b64encode(nonce + ct).decode()

  def decrypt(token: str, key: bytes) -> str:
      data = base64.urlsafe_b64decode(token)
      nonce, ct = data[:12], data[12:]
      aesgcm = AESGCM(key)
      return aesgcm.decrypt(nonce, ct, None).decode()
  ```

- **ENCRYPTION_KEY format in `.env`:** Must be exactly 32 bytes, base64-encoded. Generate with:
  ```bash
  python3 -c "import secrets, base64; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"
  ```
  Store the result (44 characters) in `.env` as `ENCRYPTION_KEY=<value>`. The `decrypt()` function must call `base64.urlsafe_b64decode(settings.ENCRYPTION_KEY)` to recover the raw 32 bytes.

- **`ENCRYPTION_KEY` vs `KITE_ENCRYPTION_KEY` — resolve the env var name.** Story 1.1's `.env.example` defined both `ENCRYPTION_KEY` and `KITE_ENCRYPTION_KEY`. This story uses `ENCRYPTION_KEY` as the single encryption key for Kite credentials. As part of this story, remove `KITE_ENCRYPTION_KEY` from `.env.example` (it was listed as a placeholder in 1.1 and is now superseded by `ENCRYPTION_KEY`). Update any reference to `KITE_ENCRYPTION_KEY` in `backend/app/core/config.py` and `.env.example`. The single key `ENCRYPTION_KEY` is used by `encryption.py` for all credential encryption in this project.

- **Never return decrypted credentials to the frontend.** The GET endpoint returns only boolean `api_key_set` and `access_token_set`. Even internal logging must not include plaintext values.

- **Single-row upsert pattern:** The `kite_settings` table holds exactly one row (one set of credentials for the whole app). The PUT endpoint should: `SELECT` the existing row → if exists, `UPDATE` → if not, `INSERT`. Alternatively, use a PostgreSQL `ON CONFLICT DO UPDATE` upsert if using raw SQL or SQLAlchemy's `insert().on_conflict_do_update()`.

- **`require_admin` dependency:** Imported from `backend/app/api/v1/dependencies.py` (created in Story 1.3). Both endpoints — GET and PUT — must use `Depends(require_admin)`. Do not inline role-checking logic inside the router.

- **Error propagation:** The encryption/decryption functions in `encryption.py` may raise `cryptography.exceptions.InvalidTag` on decryption failure (tampered ciphertext). Catch this in the service layer and raise a domain exception — not an `HTTPException` directly from the utility.

- **`cryptography` library version:** Use the latest stable version. As of the architecture document date (April 2026), this is `cryptography>=42.0`. Add it to `backend/requirements.txt`.

- **File paths — exact list to create or modify:**
  - `backend/app/core/encryption.py` (new)
  - `backend/app/core/config.py` (modify — add `ENCRYPTION_KEY` field)
  - `backend/app/models/kite_settings.py` (new)
  - `backend/alembic/versions/<timestamp>_add_kite_settings_table.py` (auto-generated)
  - `backend/app/schemas/settings.py` (new)
  - `backend/app/api/v1/settings.py` (new)
  - `backend/app/api/v1/__init__.py` (modify — register settings router)
  - `backend/app/tests/test_api_settings.py` (new)
  - `frontend/src/features/admin/AdminSettings.tsx` (new)
  - `frontend/src/App.tsx` (modify — add `/admin/settings` route)

### Project Structure Notes

- `backend/app/core/encryption.py` is a pure utility module — no FastAPI dependencies, no DB access. It accepts key bytes as a parameter so it can be unit-tested without `settings`.
- `backend/app/models/kite_settings.py` follows the same SQLModel pattern as other models (e.g. `user.py` from the template).
- `backend/app/schemas/settings.py` follows the same Pydantic pattern as `backend/app/schemas/auth.py`.
- Frontend: `AdminSettings.tsx` lives at `frontend/src/features/admin/` as specified in the architecture structure diagram.
- Do not place encryption utilities in `services/` — `core/` is the correct layer for cross-cutting security utilities.

### References

- [Source: architecture.md#Authentication & Security — Kite Connect Credential Storage]
- [Source: architecture.md#Project Structure & Boundaries — Backend Project Organization]
- [Source: architecture.md#Project Structure & Boundaries — API Boundaries (Admin-only)]
- [Source: architecture.md#Implementation Patterns & Consistency Rules — Process Patterns (Auth Dependency Injection)]
- [Source: architecture.md#Architecture Validation Results — Coherence Validation (AES-256 via cryptography library)]
- [Source: epics.md#FR38: Kite Connect API credentials stored encrypted at rest]
- [Source: epics.md#Epic 1: Foundation, Auth & Initial Setup]
- [Source: epics.md#Additional Requirements — Starter Template Init]

## Dev Agent Record

### Agent Model Used

_to be filled by dev agent_

### Debug Log References

### Completion Notes List

### File List
