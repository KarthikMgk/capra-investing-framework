# Story 1.3: Authentication Backend

Status: ready-for-dev

## Story

As a user,
I want to securely log in with email and password, receive a session that persists via an httpOnly cookie, and have that session immediately invalidated on logout,
so that only authenticated users with appropriate roles can access the application's protected resources.

## Acceptance Criteria

1. **Given** a user with valid credentials exists in the `users` table, **When** `POST /api/v1/auth/login` is called with correct `{email, password}`, **Then** the response is HTTP 200, the JSON body contains `{id, email, role}` (no token), and the response sets an `access_token` httpOnly cookie.

2. **Given** `POST /api/v1/auth/login` is called with an incorrect password, **When** the endpoint processes the request, **Then** the response is HTTP 401 with body `{"error": {"code": "INVALID_CREDENTIALS", "message": "...", "details": {}}}`.

3. **Given** a logged-in user's httpOnly cookie, **When** `POST /api/v1/auth/logout` is called, **Then** the JWT's JTI is inserted into the `revoked_tokens` table, the `access_token` cookie is cleared, and the response is HTTP 200 with `{"status": "ok"}`.

4. **Given** a JTI that has been inserted into `revoked_tokens`, **When** any protected endpoint is called using that token's cookie, **Then** the response is HTTP 401 — confirming immediate server-side invalidation.

5. **Given** a valid httpOnly cookie, **When** `GET /api/v1/auth/me` is called, **Then** the response is HTTP 200 with `{"id": "...", "email": "...", "role": "..."}`.

6. **Given** an expired JWT in the cookie (token age > 24 hours), **When** any protected endpoint is called, **Then** the response is HTTP 401.

7. **Given** a user with `role == "viewer"`, **When** a route protected by `Depends(require_admin)` is called, **Then** the response is HTTP 403 with body `{"error": {"code": "INSUFFICIENT_PERMISSIONS", "message": "...", "details": {}}}`.

8. **Given** an unauthenticated request (no cookie), **When** any protected endpoint is called, **Then** the response is HTTP 401.

9. **Given** the `ENVIRONMENT=development` setting, **When** a login succeeds, **Then** the `access_token` cookie is set with `HttpOnly=True, Secure=False, SameSite=Lax`.

10. **Given** the `ENVIRONMENT=production` setting, **When** a login succeeds, **Then** the `access_token` cookie is set with `HttpOnly=True, Secure=True, SameSite=Strict`.

11. **Given** a successful login, **When** expired rows exist in `revoked_tokens` (where `expires_at < NOW()`), **Then** those rows are deleted as part of the login transaction — preventing unbounded table growth.

12. **Given** the application starts with `FIRST_SUPERUSER_EMAIL` and `FIRST_SUPERUSER_PASSWORD` set in `.env`, **When** the backend starts for the first time, **Then** an admin user with those credentials exists in the `users` table and can successfully log in.

13. **Given** any protected route handler, **When** the handler code is inspected, **Then** JWT decoding and user lookup occur only via `Depends(get_current_user)` or `Depends(require_admin)` — never inline inside the route handler body.

## Tasks / Subtasks

- [ ] Task 1: Implement `backend/app/core/security.py` — JWT and password utilities (AC: 1, 2, 6)
  - [ ] Implement `hash_password(plain: str) -> str` using `passlib` with bcrypt scheme, cost factor 12: `CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)`
  - [ ] Implement `verify_password(plain: str, hashed: str) -> bool` using the same `CryptContext`
  - [ ] Implement `create_access_token(user_id: str, jti: str, role: str) -> str`: encode JWT with payload `{"sub": user_id, "jti": jti, "role": role, "exp": datetime.utcnow() + timedelta(hours=24)}` using HS256 and `settings.SECRET_KEY`
  - [ ] Implement `decode_token(token: str) -> dict`: decode and validate JWT; raise `AuthenticationError` on expiry or invalid signature — never raise `HTTPException` here
  - [ ] Use `PyJWT` (`import jwt`) or `python-jose`; if using PyJWT, use `jwt.decode(..., algorithms=["HS256"])`
  - [ ] Algorithm constant: define `JWT_ALGORITHM = "HS256"` in `core/constants.py` or at module level in `security.py`

- [ ] Task 2: Create `backend/app/core/exceptions.py` — domain exception hierarchy (AC: 2, 4, 7, 8)
  - [ ] Define `AuthenticationError(Exception)`: raised when JWT is missing, expired, invalid, or JTI is revoked
  - [ ] Define `AuthorizationError(Exception)`: raised when user role is insufficient
  - [ ] Define `CSVValidationError(Exception)`: raised for column mismatch or invalid data (used in Epic 2)
  - [ ] Define `KiteAPIError(Exception)`: raised for Kite Connect failures (used in Epic 3)
  - [ ] Define `ComputationError(Exception)`: raised for computation engine failures (used in Epic 3)
  - [ ] All exceptions accept a `message: str` argument and optionally a `details: dict` argument

- [ ] Task 3: Implement `backend/app/api/v1/dependencies.py` — auth dependency functions (AC: 4, 5, 6, 7, 8, 13)
  - [ ] Implement `get_current_user(request: Request, session: Session = Depends(get_session)) -> User`:
    - Extract `access_token` from `request.cookies.get("access_token")`; raise `AuthenticationError` if absent
    - Call `decode_token(token)` to get payload; raise `AuthenticationError` on any exception from decode
    - Check `revoked_tokens` table: `SELECT 1 FROM revoked_tokens WHERE jti = :jti AND expires_at > NOW()`; if row exists, raise `AuthenticationError`
    - Fetch `User` by `payload["sub"]`; raise `AuthenticationError` if not found or `is_active == False`
    - Return the `User` object
  - [ ] Implement `require_admin(user: User = Depends(get_current_user)) -> User`:
    - Check `user.role == "admin"`; if not, raise `AuthorizationError`
    - Return the `User` object
  - [ ] Add exception handlers in `main.py` (or a dedicated `exception_handlers.py`): catch `AuthenticationError` → return `JSONResponse(status_code=401, content={"error": {"code": "UNAUTHENTICATED", ...}})` and `AuthorizationError` → return `JSONResponse(status_code=403, content={"error": {"code": "INSUFFICIENT_PERMISSIONS", ...}})`

- [ ] Task 4: Create `backend/app/schemas/auth.py` — request/response schemas (AC: 1, 5)
  - [ ] Define `LoginRequest(BaseModel)` with fields: `email: str`, `password: str`
  - [ ] Define `UserResponse(BaseModel)` with fields: `id: uuid.UUID`, `email: str`, `role: str`
  - [ ] All field names use `snake_case` — never `camelCase`
  - [ ] `UserResponse` must NOT include `hashed_password`, `is_active`, or any internal fields

- [ ] Task 5: Implement `backend/app/api/v1/auth.py` — login, logout, me endpoints (AC: 1, 2, 3, 5, 9, 10, 11)
  - [ ] Implement `POST /api/v1/auth/login`:
    - Accept `LoginRequest` body; look up user by email; call `verify_password`; raise `AuthenticationError` on mismatch
    - Delete expired revoked_tokens rows: `DELETE FROM revoked_tokens WHERE expires_at < NOW()`
    - Generate a new `jti = str(uuid4())`; call `create_access_token(user_id, jti, role)`
    - Set cookie on the response:
      - `response.set_cookie(key="access_token", value=token, httponly=True, secure=(settings.ENVIRONMENT == "production"), samesite="lax" if settings.ENVIRONMENT == "development" else "strict", max_age=86400)`
    - Return `UserResponse` (id, email, role) — the JWT must NOT appear in the response body
    - Convert `AuthenticationError` to HTTP 401 at the router layer
  - [ ] Implement `POST /api/v1/auth/logout`:
    - Extract and decode token from cookie (use `decode_token`); if missing or invalid, still clear the cookie and return 200
    - Insert JTI into `revoked_tokens`: `RevokedToken(jti=payload["jti"], expires_at=datetime.utcfromtimestamp(payload["exp"]))`
    - Clear the cookie: `response.delete_cookie("access_token")`
    - Return `{"status": "ok"}`
  - [ ] Implement `GET /api/v1/auth/me`:
    - Use `current_user: User = Depends(get_current_user)`
    - Return `UserResponse(id=current_user.id, email=current_user.email, role=current_user.role)`
  - [ ] Register router in `backend/app/api/v1/__init__.py` (or wherever the router aggregation happens)

- [ ] Task 6: Wire `fastapi-csrf-protect` middleware (AC: 1, 3)
  - [ ] Add `fastapi-csrf-protect` to `requirements.txt`
  - [ ] In `backend/app/main.py`, initialise CSRF protection using Double Submit Cookie pattern
  - [ ] Apply CSRF validation to all state-mutating endpoints (`POST`, `PUT`, `PATCH`, `DELETE`) except `POST /api/v1/auth/login` (which is the initial unauthenticated entry point)
  - [ ] Document in dev notes which endpoints require the CSRF header and how the frontend must attach it (this is scaffolded here; frontend wiring is Epic frontend story)

- [ ] Task 7: Seed the initial admin user on startup (AC: 12)
  - [ ] In `backend/app/main.py`, add a startup event (or use `@app.on_event("startup")` / `lifespan` context):
    ```python
    async def seed_initial_admin():
        with Session(engine) as session:
            existing = session.exec(select(User).where(User.email == settings.FIRST_SUPERUSER_EMAIL)).first()
            if not existing:
                admin = User(
                    email=settings.FIRST_SUPERUSER_EMAIL,
                    hashed_password=hash_password(settings.FIRST_SUPERUSER_PASSWORD),
                    role="admin",
                    is_active=True,
                )
                session.add(admin)
                session.commit()
    ```
  - [ ] Add `FIRST_SUPERUSER_EMAIL` and `FIRST_SUPERUSER_PASSWORD` to `core/config.py` `Settings` class
  - [ ] The seeder must be idempotent — if the admin user already exists, skip insertion

- [ ] Task 8: Write `backend/app/tests/test_api_auth.py` (AC: 1, 2, 3, 4, 6, 7, 8)
  - [ ] Test: login with correct credentials → HTTP 200, `UserResponse` body, `access_token` cookie present
  - [ ] Test: login with wrong password → HTTP 401, error code `INVALID_CREDENTIALS`
  - [ ] Test: login with non-existent email → HTTP 401, error code `INVALID_CREDENTIALS`
  - [ ] Test: logout with valid cookie → HTTP 200, JTI inserted into `revoked_tokens`, cookie cleared
  - [ ] Test: use cookie after logout → HTTP 401 (blacklisted JTI)
  - [ ] Test: call protected endpoint with expired token → HTTP 401
  - [ ] Test: call protected endpoint with no cookie → HTTP 401
  - [ ] Test: viewer user calls admin-only route → HTTP 403
  - [ ] Test: `GET /auth/me` with valid cookie → HTTP 200, returns correct user fields
  - [ ] Test: expired `revoked_tokens` rows are deleted on next login (query count before/after)
  - [ ] Use `conftest.py` fixtures for: test DB session, an admin user, a viewer user, valid JWT cookies

## Dev Notes

- No prior implementation context — this is an initial foundation story; no existing code to reference.

- **Story dependencies:** This story depends on Story 1.1 (project scaffold) and Story 1.2 (`users` and `revoked_tokens` tables must exist before auth can run).

- **JWT stored in httpOnly cookie ONLY — CRITICAL CONSTRAINT:** The JWT must never appear in the response body, never be stored in `localStorage` or `sessionStorage`. The only correct location is the `Set-Cookie` response header with `HttpOnly=True`. Any deviation breaks the XSS protection model.

- **Cookie configuration by environment (non-negotiable):**

  | Setting | `ENVIRONMENT=development` | `ENVIRONMENT=production` |
  |---------|--------------------------|--------------------------|
  | `HttpOnly` | True | True |
  | `Secure` | False (HTTP localhost) | True (HTTPS only) |
  | `SameSite` | Lax | Strict |

  Controlled via: `settings.ENVIRONMENT == "production"` check inside the login endpoint.

- **JTI blacklist cleanup on login:** Every successful login must delete rows from `revoked_tokens` WHERE `expires_at < NOW()`. This is an indexed query (on `jti`) and has negligible overhead. Omitting this causes unbounded table growth.

- **Never raise `HTTPException` from service layer:** `security.py`, `dependencies.py`, and any service module must raise only domain exceptions (`AuthenticationError`, `AuthorizationError`, etc.). The router layer (or global exception handlers registered in `main.py`) is the ONLY place that converts domain exceptions to `HTTPException` or `JSONResponse`. This is required for testability — services must be callable without HTTP context.

- **Never inline JWT decode in route handlers:** JWT decoding and user lookup must always happen via `Depends(get_current_user)`. Every protected route must declare `current_user: User = Depends(get_current_user)` (or `Depends(require_admin)`) as a parameter. Inline decoding bypasses the auth middleware and breaks consistency.

- **bcrypt cost factor 12:** The `CryptContext` must use `bcrypt__rounds=12`. A lower value violates NFR12. Do not reduce this for performance in tests — use a test-specific fixture that creates pre-hashed passwords if test speed is a concern.

- **Error response shape:** All error responses must use the standard envelope:
  ```json
  {"error": {"code": "INVALID_CREDENTIALS", "message": "Invalid email or password.", "details": {}}}
  ```
  HTTP 401 for auth failures, HTTP 403 for role failures.

- **Required libraries (add to `requirements.txt`):**
  - `PyJWT>=2.8.0` (or `python-jose[cryptography]>=3.3.0` — pick one, be consistent)
  - `passlib[bcrypt]>=1.7.4`
  - `fastapi-csrf-protect>=0.3.3`

- **CSRF Double Submit Cookie pattern:** `fastapi-csrf-protect` must be initialised in `main.py`. State-mutating endpoints require the client to send the CSRF token in a header (`X-CSRF-Token`). The `POST /api/v1/auth/login` endpoint is exempt (it is the public auth entry point, not yet protected by a session). Full frontend wiring (Axios `withCredentials: true` + CSRF header attachment) is implemented in the Epic 1 frontend story.

- **Startup seeder idempotency:** The admin seeder must check for existence before inserting. Running `docker-compose up` multiple times must not create duplicate admin users or raise errors.

- **`GET /api/v1/auth/me` is public-facing for the frontend's `useCurrentUser` hook:** It must return exactly the `UserResponse` schema (id, email, role) — no extra fields, no token.

- **Exact file paths to create:**
  - `backend/app/core/security.py`
  - `backend/app/core/exceptions.py`
  - `backend/app/api/v1/dependencies.py`
  - `backend/app/api/v1/auth.py`
  - `backend/app/schemas/auth.py`
  - `backend/app/tests/test_api_auth.py`
  - Modified: `backend/app/main.py` (CSRF middleware, startup seeder, exception handlers)
  - Modified: `backend/app/core/config.py` (add `FIRST_SUPERUSER_EMAIL`, `FIRST_SUPERUSER_PASSWORD`, `ENVIRONMENT`)

### Project Structure Notes

- `security.py` and `exceptions.py` live in `backend/app/core/` — shared across all stories
- `dependencies.py` lives in `backend/app/api/v1/` — scoped to the v1 API layer
- `auth.py` router lives in `backend/app/api/v1/` — registered with prefix `/auth`; full path: `/api/v1/auth/login`, `/api/v1/auth/logout`, `/api/v1/auth/me`
- `schemas/auth.py` contains only Pydantic models for API I/O — no ORM models here
- Test file: `backend/app/tests/test_api_auth.py` — never co-located with source

### References

- [Source: architecture.md#Authentication & Security]
- [Source: architecture.md#Gap Analysis & Resolutions — Gap 3 (Cookie Configuration Per Environment), Gap 4 (revoked_tokens Cleanup)]
- [Source: architecture.md#Implementation Patterns & Consistency Rules — Process Patterns (Backend Error Propagation, Auth Dependency Injection)]
- [Source: architecture.md#Implementation Patterns & Consistency Rules — Anti-Patterns]
- [Source: architecture.md#Project Structure & Boundaries — Architectural Boundaries]
- [Source: architecture.md#Project Structure & Boundaries — Complete Project Directory Structure]
- [Source: epics.md#Epic 1: Foundation, Auth & Initial Setup]
- [Source: epics.md#Additional Requirements — JTI Blacklist Setup, Cookie Configuration Per Environment, Axios withCredentials]
- [Source: epics.md#FR1, FR2, FR3, FR4, FR5, FR38]

## Dev Agent Record

### Agent Model Used

_to be filled by dev agent_

### Debug Log References

### Completion Notes List

### File List
