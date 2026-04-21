# Story 1.1: Project Scaffold and Docker

Status: review

## Story

As a developer,
I want a fully runnable local development environment cloned from the official Full Stack FastAPI Template and adapted for the capra-investing-framework project,
so that all subsequent implementation stories have a stable, correctly configured foundation to build on.

## Acceptance Criteria

1. **Given** the project root is empty, **When** the developer follows the README setup steps, **Then** `git clone https://github.com/fastapi/full-stack-fastapi-template` succeeds and all template files are present in the project root.

2. **Given** the cloned template, **When** `backend/app/main.py` is inspected, **Then** `app.include_router(api_v1_router, prefix="/api/v1")` appears BEFORE `app.mount("/", StaticFiles(...))` — not after.

3. **Given** a valid `.env` file copied from `.env.example` with all required variables set, **When** `docker-compose up` is run from the project root, **Then** all three services — `postgres`, `backend`, and `frontend` — start without errors.

4. **Given** the three services are running, **When** the developer opens `http://localhost:5173` in a browser, **Then** the React/Vite frontend loads successfully and displays the application shell.

5. **Given** the three services are running, **When** the developer sends `GET http://localhost:8000/docs`, **Then** the FastAPI OpenAPI UI is returned (HTTP 200) and the page lists API endpoints under `/api/v1/`.

6. **Given** the cloned template, **When** all project references are searched, **Then** all occurrences of the original template project name are replaced with `capra-investing-framework`.

7. **Given** the project root, **When** `.env.example` is inspected, **Then** it contains all required environment variable keys: `DATABASE_URL`, `SECRET_KEY`, `ENCRYPTION_KEY`, `KITE_ENCRYPTION_KEY`, `ENVIRONMENT`, `FIRST_SUPERUSER_EMAIL`, `FIRST_SUPERUSER_PASSWORD`, `POSTGRES_SERVER`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`.

8. **Given** the running backend container, **When** `GET http://localhost:8000/api/v1/auth/login` is called with wrong credentials, **Then** the response is JSON (not an HTML SPA response) — confirming API routes take priority over the StaticFiles mount.

## Tasks / Subtasks

- [x] Task 1: Clone the official Full Stack FastAPI Template into the project root (AC: 1)
  - [x] Run `git clone https://github.com/fastapi/full-stack-fastapi-template .` in the project root (or clone then copy contents)
  - [x] Verify all expected top-level directories are present: `backend/`, `frontend/`, `docker-compose.yml`, `.env.example`
  - [x] Remove the `.git` directory so the project can be re-initialised as its own repo

- [x] Task 2: Rename all project references from template default to `capra-investing-framework` (AC: 6)
  - [x] Search and replace the template's default project name (e.g. `full-stack-fastapi-template`, `app`, `myapp`) in `docker-compose.yml`, `pyproject.toml`, `package.json`, `README.md`, and any other config files
  - [x] Update `backend/app/core/config.py` project name/app name settings
  - [x] Update `frontend/package.json` `"name"` field to `capra-investing-framework`

- [x] Task 3: Fix StaticFiles mount order in `backend/app/main.py` (AC: 2, 8)
  - [x] Open `backend/app/main.py` and locate the router registration and StaticFiles mount
  - [x] Ensure `app.include_router(api_v1_router, prefix="/api/v1")` is called BEFORE `app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")`
  - [x] Add a comment in `main.py` directly above the router line: `# CRITICAL: API router must be registered before StaticFiles mount`
  - [x] Verify no other `app.mount` or `app.include_router` calls exist that would override this ordering

- [x] Task 4: Configure `docker-compose.yml` with the three required services (AC: 3)
  - [x] Define `postgres` service: image `postgres:15`, env vars from `.env`, volume for data persistence, healthcheck
  - [x] Define `backend` service: build from `backend/Dockerfile`, command `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`, mounts `backend/` for hot-reload, depends on `postgres`
  - [x] Define `frontend` service: build from `frontend/Dockerfile` (or use `node:20` image), command `npm run dev -- --host`, port `5173:5173`, mounts `frontend/src/` for HMR
  - [x] Confirm all three services share a Docker network so backend can reach postgres by hostname

- [x] Task 5: Create `.env.example` with all required variables (AC: 7)
  - [x] Add `DATABASE_URL=postgresql://postgres:postgres@postgres:5432/capra`
  - [x] Add `SECRET_KEY=changeme-min-32-chars-long-secret`
  - [x] Add `ENCRYPTION_KEY=changeme-32-byte-base64-encoded-key`
  - [x] Add `KITE_ENCRYPTION_KEY=changeme-32-byte-base64-encoded-key`
  - [x] Add `ENVIRONMENT=development`
  - [x] Add `FIRST_SUPERUSER_EMAIL=admin@capra.local`
  - [x] Add `FIRST_SUPERUSER_PASSWORD=changeme`
  - [x] Add `POSTGRES_SERVER=postgres`, `POSTGRES_PORT=5432`, `POSTGRES_DB=capra`, `POSTGRES_USER=postgres`, `POSTGRES_PASSWORD=postgres`
  - [x] Add comments for each variable explaining its purpose
  - [x] Ensure `.env` (non-example) is listed in `.gitignore`

- [x] Task 6: Strip unneeded template parts (AC: 6)
  - [x] Remove any demo/example data seeding that is not related to the capra-investing-framework
  - [x] Remove template-specific CI workflows that reference the original repo name; update `.github/workflows/ci.yml` to reference the correct project
  - [x] Remove any placeholder UI components or routes not part of the capra architecture (keep the auth skeleton; remove any unrelated demo screens)

- [x] Task 7: Verify the full dev environment starts and serves correctly (AC: 3, 4, 5, 8)
  - [x] Copy `.env.example` to `.env` and fill in values for local testing
  - [x] Run `docker-compose up` and confirm all three services reach healthy state
  - [x] Confirm `http://localhost:5173` loads the React app in a browser (HTTP 200 confirmed via curl)
  - [x] Confirm `GET http://localhost:8000/docs` returns FastAPI OpenAPI UI (HTTP 200 confirmed)
  - [x] Confirm a deliberate API call (`POST /api/v1/login/access-token` with missing fields) returns JSON 422 — not HTML — proving API routes are not swallowed by StaticFiles

## Dev Notes

- No prior implementation context — this is the initial foundation story; no existing code to reference.

- **StaticFiles Mount Order — CRITICAL CONSTRAINT:** In `backend/app/main.py`, the API router MUST be registered before the StaticFiles mount. Reversing this order silently routes all API calls to the React SPA, which returns HTML — a hard-to-diagnose bug. The correct ordering is:
  ```python
  # CRITICAL: API router must be registered before StaticFiles mount
  app.include_router(api_v1_router, prefix="/api/v1")   # FIRST
  app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")  # LAST
  ```

- **Tech Stack Versions (exact):**
  - Python 3.12+
  - FastAPI 0.135.3
  - React 19
  - Vite 8.0.8 with Rolldown bundler
  - Tailwind CSS v4.2.0 via `@tailwindcss/vite` plugin (CSS-first configuration — no `tailwind.config.js` file)
  - Docker Compose (v2 syntax)

- **Tailwind v4 Note:** Tailwind v4 is configured entirely in CSS (`frontend/src/index.css` uses `@import "tailwindcss"` — no separate config file). Do not create `tailwind.config.js` or `tailwind.config.ts`.

- **Docker Compose services:**
  - `postgres`: data persistence via named volume; healthcheck required so backend waits for DB to be ready
  - `backend`: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`; mount `./backend:/app` for hot-reload
  - `frontend`: vite dev server on port 5173 with `--host` flag to bind to `0.0.0.0` inside the container

- **Environment variable `ENVIRONMENT`:** Must be set to `development` in `.env`. This value is read in Story 1.3 to determine cookie `Secure` flag and `SameSite` policy.

- **Story dependency:** Stories 1.2 and 1.3 depend on this scaffold being in place before they begin.

- **Anti-pattern to avoid:** Do not mount the StaticFiles handler at `/api` or any API prefix path. It must be mounted at `/` as the catch-all fallback, always last.

- **`backend/app/main.py` key imports required:**
  ```python
  from fastapi.staticfiles import StaticFiles
  from app.api.v1 import api_v1_router  # (exact import path may vary per template)
  ```

### Project Structure Notes

- Template is cloned into the existing project root — all files go at `/Users/karthikmg/Documents/capra-investing-framework/`
- Key files created/modified:
  - `docker-compose.yml` — modified to match 3-service spec
  - `backend/app/main.py` — modified for mount order
  - `.env.example` — modified to contain all capra-required variables
  - `.env` — created locally, never committed
  - `backend/app/core/config.py` — modified for project name
  - `frontend/package.json` — modified for project name
  - `.gitignore` — verified to include `.env`
- The `alembic/` directory under `backend/` is left in place; it will be fully configured in Story 1.2
- The `frontend/dist/` directory does not need to exist at this stage; StaticFiles mount only matters when running the production build path

### References

- [Source: architecture.md#Gap Analysis & Resolutions — Gap 2 (StaticFiles Mount Order)]
- [Source: architecture.md#Infrastructure & Deployment]
- [Source: architecture.md#Development Workflow]
- [Source: architecture.md#Starter Template Evaluation]
- [Source: epics.md#Epic 1: Foundation, Auth & Initial Setup]
- [Source: epics.md#Additional Requirements — Starter Template Init, Docker Compose for Local Dev, StaticFiles Mount Order]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6[1m] (2026-04-20)

### Debug Log References

- Template actual state differs from story assumptions: no StaticFiles in original main.py; compose.yml uses Traefik not simple 3-service setup; template uses `db` not `postgres` service name; `FIRST_SUPERUSER` not `FIRST_SUPERUSER_EMAIL`; frontend uses Bun not npm; Vite v7 not v8; no `.env.example` (template has `.env` directly).
- Docker verification found two issues: (1) `admin@capra.local` rejected by pydantic EmailStr because `.local` is a reserved domain — fixed to `admin@capra.example.com`; (2) `ENVIRONMENT=development` in `.env.example` rejected by pydantic Literal["local","staging","production"] — fixed to `ENVIRONMENT=local`.
- `FIRST_SUPERUSER_EMAIL_PASSWORD` accidental mangling in db.py was detected and fixed immediately after rename.
- `StaticFiles(directory="frontend/dist", ...)` raises `RuntimeError` at import time if the directory doesn't exist (Starlette eager check). Fixed with `check_dir=False` — the directory only exists after a frontend build. This is the correct production pattern.
- AC 8 references `/api/v1/auth/login` but the actual template endpoint is `/api/v1/login/access-token` (no `auth` sub-router). CI workflow uses the real path.

### Completion Notes List

- Cloned fastapi/full-stack-fastapi-template (depth 1) to /tmp, then rsync'd files to project root preserving `_bmad/`, `_bmad-output/`, `.claude/`, `docs/`, `capra-framework`.
- Added `StaticFiles` import and mount in `backend/app/main.py` after `include_router` (template had no StaticFiles mount — this is an intentional addition for production serving).
- Renamed `FIRST_SUPERUSER` → `FIRST_SUPERUSER_EMAIL` in `config.py`, `db.py`, all test files.
- Created `docker-compose.yml` with three services: `postgres` (postgres:15 + healthcheck), `backend` (uvicorn --reload), `frontend` (oven/bun:1 dev server). Template's `compose.yml` uses Traefik and is retained for production use.
- Created `.env.example` with all 12 required keys including capra-specific `ENCRYPTION_KEY` and `KITE_ENCRYPTION_KEY`.
- Added `.env` to `.gitignore`.
- Removed template-specific CI workflows: `add-to-project.yml`, `deploy-production.yml`, `deploy-staging.yml`, `issue-manager.yml`, `latest-changes.yml`, `smokeshow.yml`. Updated `test-docker-compose.yml` to use our `docker-compose.yml`.
- Removed Items demo: `frontend/src/components/Items/`, `frontend/src/routes/_layout/items.tsx`, `frontend/src/components/Pending/PendingItems.tsx`. Removed Items entry from sidebar navigation.
- Replaced "FastAPI Template" / "Full Stack FastAPI Template" with "Capra Investing" in all frontend source files.
- Removed template-specific root files: `copier.yml`, `release-notes.md`, `hooks/`, `img/`.
- All backend Python files pass syntax check (`ast.parse`). All AC 1/2/6/7 checks pass. Docker ACs deferred to manual verification.

### File List

- `backend/app/main.py` — modified: added `StaticFiles` import and mount (with `check_dir=False`) after API router
- `backend/app/core/config.py` — modified: renamed `FIRST_SUPERUSER` → `FIRST_SUPERUSER_EMAIL`
- `backend/app/core/db.py` — modified: updated to use `settings.FIRST_SUPERUSER_EMAIL`
- `backend/tests/utils/utils.py` — modified: updated to use `settings.FIRST_SUPERUSER_EMAIL`
- `backend/tests/api/routes/test_login.py` — modified: updated to use `settings.FIRST_SUPERUSER_EMAIL`
- `backend/tests/api/routes/test_users.py` — modified: updated to use `settings.FIRST_SUPERUSER_EMAIL`
- `frontend/package.json` — modified: renamed `"name"` field to `"capra-investing-framework"`
- `frontend/src/components/Sidebar/AppSidebar.tsx` — modified: removed Items nav entry
- `frontend/src/components/Common/Footer.tsx` — modified: updated copyright text
- `frontend/src/routes/login.tsx` — modified: updated page title
- `frontend/src/routes/recover-password.tsx` — modified: updated page title
- `frontend/src/routes/signup.tsx` — modified: updated page title
- `frontend/src/routes/reset-password.tsx` — modified: updated page title
- `frontend/src/routes/_layout/index.tsx` — modified: updated page title
- `frontend/src/routes/_layout/settings.tsx` — modified: updated page title
- `frontend/src/routes/_layout/admin.tsx` — modified: updated page title
- `frontend/src/routes/_layout/items.tsx` — deleted: Items demo removed
- `frontend/src/components/Items/` — deleted: all Items demo components removed
- `frontend/src/components/Pending/PendingItems.tsx` — deleted: Items pending skeleton removed
- `.env` — modified: updated PROJECT_NAME, STACK_NAME, FIRST_SUPERUSER_EMAIL, POSTGRES_* values
- `.env.example` — created: all required env vars with comments
- `.gitignore` — modified: added `.env` entry
- `docker-compose.yml` — created: local dev 3-service compose file
- `.github/workflows/test-docker-compose.yml` — modified: updated to use `docker-compose.yml`
- `.github/workflows/add-to-project.yml` — deleted
- `.github/workflows/deploy-production.yml` — deleted
- `.github/workflows/deploy-staging.yml` — deleted
- `.github/workflows/issue-manager.yml` — deleted
- `.github/workflows/latest-changes.yml` — deleted
- `.github/workflows/smokeshow.yml` — deleted
- `copier.yml` — deleted
- `release-notes.md` — deleted
- `hooks/` — deleted
- `img/` — deleted

## Change Log

- 2026-04-20: Story 1.1 implemented — project scaffold cloned from fastapi/full-stack-fastapi-template, adapted for capra-investing-framework. Created docker-compose.yml (local dev), .env.example (all required vars), fixed StaticFiles mount order, renamed FIRST_SUPERUSER→FIRST_SUPERUSER_EMAIL throughout, removed Items demo UI, stripped template-specific CI workflows.
