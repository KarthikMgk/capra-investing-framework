# Story 6.1: User Management Backend

Status: ready-for-dev

## Story

As an admin user,
I want backend API endpoints to create, view, update, and delete user accounts with role assignment,
so that access to the application can be managed without manual database intervention.

## Acceptance Criteria

1. **Given** an admin user calls `GET /api/v1/users`, **When** the request is processed, **Then** the response is `{ "items": [...], "total": N }` listing all users with `id`, `email`, `role`, `is_active`, and `created_at` fields — no `hashed_password` field in any response object.

2. **Given** an admin user calls `POST /api/v1/users` with `{ "email": "user@example.com", "password": "secretpass", "role": "viewer" }`, **When** the request is processed, **Then** the user is created with the password hashed using bcrypt cost 12, and the response is HTTP 201 with the `UserResponse` (no password field).

3. **Given** a Viewer-role user calls any `/api/v1/users` endpoint (`GET`, `POST`, `PATCH`, or `DELETE`), **When** the request is processed, **Then** the response is HTTP 403 Forbidden.

4. **Given** an unauthenticated request to any `/api/v1/users` endpoint, **When** the request is processed, **Then** the response is HTTP 401 Unauthorized.

5. **Given** an admin user calls `POST /api/v1/users` with an email that already exists in the `users` table, **When** the request is processed, **Then** the response is HTTP 409 Conflict — NOT HTTP 422 or HTTP 500.

6. **Given** an admin user calls `PATCH /api/v1/users/{user_id}` with `{ "is_active": false }`, **When** the request is processed, **Then** the user's `is_active` field is set to `false` and the updated `UserResponse` is returned.

7. **Given** a user has `is_active=false`, **When** that user attempts to log in via `POST /api/v1/auth/login`, **Then** the login is rejected (HTTP 401) — `get_current_user` checks `is_active` and raises 401 for deactivated users.

8. **Given** an admin user calls `PATCH /api/v1/users/{user_id}` with `{ "role": "admin" }`, **When** the request is processed, **Then** the user's role is updated to `"admin"` and the updated `UserResponse` is returned.

9. **Given** an admin user calls `DELETE /api/v1/users/{user_id}` where `user_id` is a different user's ID, **When** the request is processed, **Then** the user is permanently deleted and the response is HTTP 204 with no body.

10. **Given** an admin user calls `DELETE /api/v1/users/{user_id}` where `user_id` is their OWN user ID, **When** the request is processed, **Then** the response is HTTP 400 or HTTP 403, preventing self-deletion.

11. **Given** a `GET /api/v1/users/{user_id}` call is made for a non-existent user ID, **When** the request is processed, **Then** the response is HTTP 404.

12. **Given** `POST /api/v1/users` accepts a `role` field, **When** any value other than `"admin"` or `"viewer"` is submitted, **Then** the response is HTTP 422 (Pydantic validation failure) — no other role values are accepted.

## Tasks / Subtasks

- [ ] Task 1: Create `backend/app/schemas/user.py` — user management Pydantic schemas (AC: 1, 2, 6, 8, 12)
  - [ ] Define `UserCreate { email: EmailStr, password: str, role: Literal["admin", "viewer"] }`
  - [ ] Define `UserUpdate { is_active: bool | None = None, role: Literal["admin", "viewer"] | None = None }` — both fields optional, at least one must be provided
  - [ ] Define `UserResponse { id: UUID, email: str, role: str, is_active: bool, created_at: str }` — `created_at` as ISO 8601 UTC string
  - [ ] `UserResponse` must NOT include `hashed_password` — never expose it
  - [ ] All field names `snake_case`
  - [ ] Use `Literal["admin", "viewer"]` (not `str`) for `role` in `UserCreate` and `UserUpdate` to enforce allowed values at Pydantic level

- [ ] Task 2: Create `backend/app/api/v1/users.py` — user management endpoints (AC: 1, 2, 3, 4, 5, 6, 8, 9, 10, 11)
  - [ ] Define `GET /api/v1/users` with `Depends(require_admin)`:
    - Query all rows from `users` table
    - Return `{ "items": [UserResponse, ...], "total": N }`
  - [ ] Define `POST /api/v1/users` with `Depends(require_admin)`:
    - Accept `UserCreate` request body
    - Check if `email` already exists — if so, raise `HTTPException(status_code=409, detail={"error": {"code": "DUPLICATE_EMAIL", "message": "A user with this email already exists."}})`
    - Hash the password using `bcrypt` at cost 12 via the `hash_password()` function from `core/security.py`
    - Insert new `User` row into DB
    - Return HTTP 201 with `UserResponse`
  - [ ] Define `PATCH /api/v1/users/{user_id}` with `Depends(require_admin)`:
    - Accept `UserUpdate` request body (partial update — `is_active` and/or `role`)
    - Fetch user by `user_id` — return 404 if not found
    - Apply only the fields present in `UserUpdate` (non-None values)
    - Save and return updated `UserResponse`
  - [ ] Define `DELETE /api/v1/users/{user_id}` with `Depends(require_admin)`:
    - Check if `user_id == current_user.id` — if so, raise `HTTPException(status_code=400, detail={"error": {"code": "CANNOT_DELETE_SELF", "message": "Admins cannot delete their own account."}})`
    - Fetch user by `user_id` — return 404 if not found
    - Hard delete the user row
    - Return HTTP 204 with no body
  - [ ] Register the users router in `backend/app/main.py` or `backend/app/api/v1/__init__.py`

- [ ] Task 3: Enforce `is_active` at both login and auth middleware (AC: 7)
  - [ ] Open `backend/app/api/v1/auth.py` (from Epic 1 — do NOT re-create): in the `POST /auth/login` handler, after looking up the user by email and verifying the password, add `if not user.is_active: raise HTTPException(status_code=401, detail={"error": {"code": "ACCOUNT_DISABLED", "message": "This account has been deactivated."}})` — login occurs before any JWT is issued, so `get_current_user` is NOT involved here
  - [ ] Open `backend/app/api/v1/dependencies.py` (from Epic 1 — do NOT re-create): verify `get_current_user` also raises HTTP 401 if `user.is_active == False` after fetching the user from DB — this blocks deactivated users on subsequent requests even if they hold a valid token issued before deactivation
  - [ ] Both checks are required: the login check blocks new sessions; the `get_current_user` check blocks existing sessions mid-flight

- [ ] Task 4: Write `backend/app/tests/test_api_users.py` (AC: 1, 2, 3, 4, 5, 6, 7, 9, 10)
  - [ ] Test: Viewer calling `GET /api/v1/users` returns HTTP 403
  - [ ] Test: Viewer calling `POST /api/v1/users` returns HTTP 403
  - [ ] Test: Viewer calling `PATCH /api/v1/users/{id}` returns HTTP 403
  - [ ] Test: Viewer calling `DELETE /api/v1/users/{id}` returns HTTP 403
  - [ ] Test: Unauthenticated request to `GET /api/v1/users` returns HTTP 401
  - [ ] Test: Admin creates a new viewer user — user appears in `GET /api/v1/users` response
  - [ ] Test: Admin creates user with duplicate email — returns HTTP 409
  - [ ] Test: Admin calls `PATCH /api/v1/users/{id}` with `is_active=false` — user is deactivated
  - [ ] Test: Deactivated user attempts login via `POST /api/v1/auth/login` — returns HTTP 401
  - [ ] Test: Admin hard-deletes a user — user no longer appears in list
  - [ ] Test: Admin calls `DELETE /api/v1/users/{own_id}` — returns HTTP 400 or HTTP 403
  - [ ] Use `conftest.py` fixtures for test DB, admin auth cookie, and viewer auth cookie

## Dev Notes

- **All `/users` endpoints require `Depends(require_admin)`:** Never use `Depends(get_current_user)` on user management routes. A Viewer calling any of these endpoints must receive HTTP 403. Import `require_admin` from `backend/app/api/v1/dependencies.py` (established in Epic 1).
- **Passwords hashed with bcrypt cost 12 — NEVER stored in plaintext:** Use the `hash_password()` function from `backend/app/core/security.py` (established in Epic 1). Never call `bcrypt` directly from the router — go through the security module. Cost factor MUST be 12 per NFR12.
- **`UserResponse` never includes `hashed_password`:** The `UserResponse` Pydantic schema must not have a `hashed_password` field. Verify with `model_validate` / `model_dump` that the hash is excluded from all serialized responses.
- **Duplicate email returns 409 Conflict:** Do NOT let PostgreSQL's unique constraint raise an unhandled 500. Catch the `IntegrityError` (SQLAlchemy) or explicitly check for existing email before insert. Return `HTTPException(status_code=409, ...)` with the standard error envelope.
- **`is_active` check — TWO locations required:** (1) In `backend/app/api/v1/auth.py` login handler: after password verification, check `if not user.is_active` and raise HTTP 401 with code `ACCOUNT_DISABLED`. The login path does NOT go through `get_current_user` — the user has no token yet — so the login handler itself must own this check. (2) In `backend/app/api/v1/dependencies.py` `get_current_user`: also add `if not user.is_active: raise HTTPException(401)` after fetching the user from DB. This blocks deactivated users who hold a previously issued valid token. Both checks are required — missing either one creates a bypass.
- **Self-deletion guard:** The `DELETE /api/v1/users/{user_id}` handler receives the current admin from `Depends(require_admin)`. Compare `user_id == current_user.id` before executing the delete. Return HTTP 400 with code `CANNOT_DELETE_SELF`.
- **PATCH is partial update:** `UserUpdate` uses `Optional` fields. Only update the fields that are not `None` in the request body. If both `is_active` and `role` are `None`, return HTTP 422 (Pydantic will enforce this naturally if you add a validator).
- **`UserResponse.created_at` as ISO 8601 string:** Serialize `created_at` as `"2026-04-17T10:30:00Z"` (UTC, with Z suffix). Use `model_config = ConfigDict(json_encoders={datetime: lambda dt: dt.isoformat() + "Z"})` or a Pydantic `field_serializer`.
- **`users` table already exists:** The `users` table and the `User` SQLModel were created in Story 1.2. Do NOT re-create the model. Import `User` from `backend/app/models/user.py`.
- **`backend/app/schemas/user.py` — check if partially exists:** The auth schemas are in `backend/app/schemas/auth.py` (from Epic 1). Create a new `user.py` file in `schemas/` for the user management schemas (`UserCreate`, `UserUpdate`, `UserResponse`). Do not add them to `auth.py`.
- **First superuser:** The first admin user is created by the seeder from Story 1.1 (using `FIRST_SUPERUSER_EMAIL` and `FIRST_SUPERUSER_PASSWORD` env vars). Test fixtures should use this existing admin or create a test-specific admin via the DB session directly.
- **Error envelope shape (exact):**
  - Duplicate email: `{"error": {"code": "DUPLICATE_EMAIL", "message": "A user with this email already exists."}}`
  - Self-delete: `{"error": {"code": "CANNOT_DELETE_SELF", "message": "Admins cannot delete their own account."}}`
  - Not found: `{"error": {"code": "USER_NOT_FOUND", "message": "User not found."}}`

### Project Structure Notes

- Files to CREATE:
  - `backend/app/api/v1/users.py`
  - `backend/app/schemas/user.py`
  - `backend/app/tests/test_api_users.py`
- Files to MODIFY:
  - `backend/app/api/v1/auth.py` — add `is_active` check in login handler after password verification
  - `backend/app/api/v1/dependencies.py` — add `is_active` check to `get_current_user` if not present
  - `backend/app/main.py` or `backend/app/api/v1/__init__.py` — register users router

### References

- [Source: architecture.md#Structure Patterns — Backend Project Organization]
- [Source: architecture.md#Architectural Boundaries — API Boundaries (Admin-only)]
- [Source: architecture.md#Process Patterns — Auth Dependency Injection]
- [Source: architecture.md#Process Patterns — Backend Error Propagation]
- [Source: architecture.md#Format Patterns — HTTP Status Codes]
- [Source: architecture.md#Naming Patterns — JSON Field Naming Critical Rule]
- [Source: epics.md#Epic 6: User Management]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
