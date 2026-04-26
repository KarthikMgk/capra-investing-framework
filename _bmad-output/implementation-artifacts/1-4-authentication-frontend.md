# Story 1.4: Authentication Frontend

Status: done

## Story

As a user,
I want a login page that authenticates me and protects all other routes based on my role,
so that only authenticated users can access the app and only admins can reach admin-only screens.

## Acceptance Criteria

1. **Given** a visitor is not authenticated, **When** they navigate to any protected route (e.g. `/`), **Then** they are immediately redirected to `/login` before any protected content renders.

2. **Given** the `/login` page is displayed, **When** the user submits valid email and password credentials, **Then** the app POSTs to `POST /api/v1/auth/login`, receives an httpOnly cookie, and navigates to `/` — no JWT is stored in localStorage or component state.

3. **Given** the `/login` page is displayed, **When** the user submits invalid credentials, **Then** an inline error message appears below the form (not a modal, not a toast) and the form remains interactive.

4. **Given** an authenticated user is on any page, **When** they trigger logout, **Then** the app POSTs to `POST /api/v1/auth/logout` and is redirected to `/login`.

5. **Given** the Axios instance is configured, **When** any API request is made, **Then** the request includes cookies automatically because `withCredentials: true` is set globally on the instance — not per-request.

6. **Given** any API request returns a 401 response, **When** the Axios 401 interceptor fires, **Then** the user is redirected to `/login` — no individual component needs to handle 401 separately.

7. **Given** an authenticated user with `role === "viewer"` navigates to an `AdminRoute`-wrapped path, **When** the route guard checks their role, **Then** they see a 403 message or are redirected — they never see admin content.

8. **Given** the app is loading the current user from `GET /api/v1/auth/me`, **When** the request is in-flight, **Then** a spinner is displayed in place of the route content — the page is never blank and is not disabled.

9. **Given** `useCurrentUser()` is implemented, **When** inspected, **Then** it uses TanStack Query (`useQuery`) — not `useState` + `useEffect` — for the `GET /api/v1/auth/me` call.

10. **Given** the `LoginPage.test.tsx` test suite, **When** it runs, **Then** it covers: renders the email and password form fields, shows inline error on bad credentials (mocked 401 response), and navigates to `/` on success (mocked 200 response).

## Tasks / Subtasks

- [ ] Task 1: Create shared TypeScript types (AC: 2, 7)
  - [ ] Create `frontend/src/shared/types/user.ts`: export `UserRole = "admin" | "viewer"` and `User { id: string; email: string; role: UserRole }`
  - [ ] Create `frontend/src/shared/types/api.ts`: export `ApiError { error: { code: string; message: string; details?: unknown } }` and `ApiCollection<T> { items: T[]; total: number }`

- [ ] Task 2: Create Axios API client with global `withCredentials` and 401 interceptor (AC: 5, 6)
  - [ ] Create `frontend/src/shared/lib/apiClient.ts`
  - [ ] Instantiate Axios with `baseURL: ""` (same-origin — no hardcoded host) and `withCredentials: true` set at the instance level (never per-request)
  - [ ] Add a response interceptor: on 401, call `window.location.href = "/login"` (or `navigate("/login")` if router context is accessible) and reject the promise
  - [ ] Export the instance as the default export

- [ ] Task 3: Create TanStack Query client (AC: 9)
  - [ ] Create `frontend/src/shared/lib/queryClient.ts`
  - [ ] Instantiate `QueryClient` with `defaultOptions: { queries: { staleTime: 5 * 60 * 1000, retry: 1 } }`
  - [ ] Export the instance as `queryClient`

- [ ] Task 4: Create auth hooks using TanStack Query (AC: 2, 4, 9)
  - [ ] Create `frontend/src/features/auth/useAuth.ts`
  - [ ] Implement `useCurrentUser()`: `useQuery({ queryKey: ["currentUser"], queryFn: () => apiClient.get<User>("/api/v1/auth/me").then(r => r.data) })`
  - [ ] Implement `useLogin()`: `useMutation` that POSTs `{ email, password }` to `/api/v1/auth/login`; on success, invalidates `["currentUser"]` query and navigates to `/`
  - [ ] Implement `useLogout()`: `useMutation` that POSTs to `/api/v1/auth/logout`; on success, invalidates all queries and navigates to `/login`

- [ ] Task 5: Create LoginPage component (AC: 2, 3)
  - [ ] Create `frontend/src/features/auth/LoginPage.tsx`
  - [ ] Render a form with `type="email"` and `type="password"` inputs plus a submit button
  - [ ] On submit, call `useLogin()` mutation with form values
  - [ ] On mutation success: navigate to `/` (handled inside the hook)
  - [ ] On mutation error: display the error message inline below the form — not a modal, not a toast
  - [ ] Show a loading indicator on the submit button while the mutation is pending

- [ ] Task 6: Create ProtectedRoute component (AC: 1, 8)
  - [ ] Create `frontend/src/shared/components/ProtectedRoute.tsx`
  - [ ] Call `useCurrentUser()` inside the component
  - [ ] While loading (`isLoading`): render a centered `<LoadingSpinner />` component
  - [ ] On error or unauthenticated (query returns 401 / `isError`): `<Navigate to="/login" replace />`
  - [ ] On success with valid user: render `<Outlet />` (or `{children}` if using wrapper pattern)

- [ ] Task 7: Create AdminRoute component (AC: 7)
  - [ ] Create `frontend/src/shared/components/AdminRoute.tsx`
  - [ ] Compose with `ProtectedRoute` — i.e., `AdminRoute` only renders its children if `ProtectedRoute` has already confirmed a valid user
  - [ ] After authentication confirmed: check `user.role === "admin"` — if not admin, render an inline 403 message (`<p>Access denied. Admin role required.</p>`) or redirect; do not expose admin content

- [ ] Task 8: Create LoadingSpinner and ErrorMessage shared components (AC: 8)
  - [ ] Create `frontend/src/shared/components/LoadingSpinner.tsx`: a simple centered spinner using Tailwind `animate-spin`
  - [ ] Create `frontend/src/shared/components/ErrorMessage.tsx`: accepts `message: string` prop, renders inline error text styled with Tailwind red

- [ ] Task 9: Wire App.tsx with React Router v7 and route guards (AC: 1, 2, 7)
  - [ ] Open `frontend/src/App.tsx` (created in Story 1.1 scaffold; modify — do not recreate from scratch)
  - [ ] Wrap the app in `<QueryClientProvider client={queryClient}>` and `<BrowserRouter>` (or `RouterProvider` for data router)
  - [ ] Define `/login` as a public route (no guard)
  - [ ] Define all other routes wrapped with `<ProtectedRoute>` (renders children only when authenticated)
  - [ ] Define admin routes (`/upload`, `/admin/settings`, `/admin/users`) additionally wrapped with `<AdminRoute>`
  - [ ] Ensure a catch-all or index route redirects to a sensible default when authenticated

- [ ] Task 10: Write LoginPage tests (AC: 10)
  - [ ] Create `frontend/src/features/auth/LoginPage.test.tsx`
  - [ ] Test: renders email input, password input, and submit button
  - [ ] Test: when mutation returns a 401 error (mocked via `msw` or `vi.fn()`), an inline error message appears in the DOM
  - [ ] Test: when mutation returns success (mocked 200), `window.location` or router navigation leads to `/`
  - [ ] Use Vitest + React Testing Library (already configured in template)

## Dev Notes

- No prior implementation context — this is an early story in the sprint. Stories 1.1 (scaffold), 1.2 (migrations), and 1.3 (auth backend) must be complete before this story's API calls function end-to-end. The frontend code can be written and unit-tested with mocked API calls before 1.3 is merged.

- **`withCredentials: true` — CRITICAL:** Must be set on the Axios instance at construction time, not added per-request. httpOnly cookies are silently dropped by the browser if `withCredentials` is absent. Example:
  ```typescript
  // frontend/src/shared/lib/apiClient.ts
  import axios from "axios";
  const apiClient = axios.create({ withCredentials: true });
  export default apiClient;
  ```
  Any per-request override of `withCredentials: false` breaks the auth flow.

- **Never store JWT in localStorage or component state.** The httpOnly cookie is set by the backend on login and sent automatically by the browser on all subsequent requests. There is no token variable in the React app.

- **401 interceptor is the only place 401 is handled — with one critical exception.** Individual components must not catch 401 errors; the Axios interceptor handles them centrally. However, the interceptor MUST skip the redirect-to-login behavior when the failing request URL is `/api/v1/auth/login` or `/api/v1/auth/me`. Without this guard: a bad-password login attempt (401 from `/auth/login`) would redirect the user away from the login page before the inline error message in AC3 is ever shown; and the initial `useCurrentUser()` call (401 from `/auth/me` when unauthenticated) would cause a redirect loop. Implementation pattern:
  ```typescript
  apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
      const url: string = error.config?.url ?? "";
      const isAuthEndpoint = url.includes("/auth/login") || url.includes("/auth/me");
      if (error.response?.status === 401 && !isAuthEndpoint) {
        window.location.href = "/login";
      }
      return Promise.reject(error);
    }
  );
  ```
  Components only handle non-401 application errors (e.g. 400 validation errors from upload).

- **TanStack Query v5 — do not use `useState` + `useEffect` for server data.** The pattern `const [user, setUser] = useState(null); useEffect(() => fetch("/auth/me").then(setUser), [])` is an explicit anti-pattern per the architecture. Use `useQuery` and `useMutation` from `@tanstack/react-query`.

- **`useCurrentUser` location:** Architecture shows it at `shared/hooks/useCurrentUser.ts` as a shared hook, but it is also referenced in `features/auth/useAuth.ts`. Implement it in `features/auth/useAuth.ts` and re-export from `shared/hooks/useCurrentUser.ts` to satisfy both patterns:
  ```typescript
  // frontend/src/shared/hooks/useCurrentUser.ts
  export { useCurrentUser } from "@/features/auth/useAuth";
  ```

- **React Router v7 pattern:** Use `<Outlet />` inside `ProtectedRoute` and `AdminRoute` for nested route layouts, or use render-prop/children pattern. The exact pattern depends on whether data routers (`createBrowserRouter`) or JSX routers (`<BrowserRouter>`) are used — the template may pre-configure one; match existing template conventions rather than switching.

- **Snake_case JSON fields:** All API response fields are `snake_case` — `user.role`, not `user.Role`. TypeScript types must match this exactly. No camelCase conversion layer.

- **File paths — exact list to create:**
  - `frontend/src/shared/types/user.ts` (new)
  - `frontend/src/shared/types/api.ts` (new)
  - `frontend/src/shared/lib/apiClient.ts` (new)
  - `frontend/src/shared/lib/queryClient.ts` (new)
  - `frontend/src/features/auth/useAuth.ts` (new)
  - `frontend/src/features/auth/LoginPage.tsx` (new)
  - `frontend/src/features/auth/LoginPage.test.tsx` (new)
  - `frontend/src/shared/components/ProtectedRoute.tsx` (new)
  - `frontend/src/shared/components/AdminRoute.tsx` (new)
  - `frontend/src/shared/components/LoadingSpinner.tsx` (new)
  - `frontend/src/shared/components/ErrorMessage.tsx` (new)
  - `frontend/src/shared/hooks/useCurrentUser.ts` (new — re-export only)
  - `frontend/src/App.tsx` (modify existing — add routes alongside any existing scaffold)

### Project Structure Notes

- All new files are under `frontend/src/` per the architecture's feature-grouped structure.
- Component files use `PascalCase.tsx`; non-component files use `camelCase.ts`.
- Test files are co-located: `LoginPage.test.tsx` lives next to `LoginPage.tsx`.
- `shared/components/` is for truly shared UI primitives only — not feature-specific components.
- Do not create a `shared/hooks/` directory if it doesn't exist — create the directory as part of this story.

### References

- [Source: architecture.md#Authentication & Security — JWT Token Storage]
- [Source: architecture.md#Frontend Architecture — Server State Management, HTTP Client, Routing]
- [Source: architecture.md#Project Structure & Boundaries — Frontend Project Organization]
- [Source: architecture.md#Implementation Patterns & Consistency Rules — Naming Patterns (TypeScript), Anti-Patterns]
- [Source: architecture.md#Gap Analysis & Resolutions — Gap 3 (Cookie Configuration Per Environment)]
- [Source: architecture.md#Additional Requirements — Axios withCredentials: true]
- [Source: epics.md#Epic 1: Foundation, Auth & Initial Setup]
- [Source: epics.md#Additional Requirements — Axios withCredentials: true]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6 (1M context)

### Completion Notes List

- Used TanStack Router (file-based routing) instead of React Router — matched existing template conventions
- `features/auth/useAuth.ts` is the primary auth hook; `hooks/useAuth.ts` re-exports it for backward compat
- `isLoggedIn()` stub exported as `() => false` to keep template routes (signup, recover-password, reset-password) compiling without changes
- `OpenAPI.WITH_CREDENTIALS = true` set in main.tsx so auto-generated client sends cookies alongside new apiClient
- `_layout.tsx` beforeLoad uses `queryClient.ensureQueryData(currentUserQueryOptions)` — redirects on any error
- `_layout/admin.tsx` beforeLoad checks `user.role === "admin"` (was `is_superuser`)
- Skipped ProtectedRoute/AdminRoute components (spec was React Router; TanStack Router uses beforeLoad instead)
- Login form updated from `username` → `email` field to match backend `LoginRequest`
- Tests co-located at `features/auth/LoginPage.test.tsx` — explicit `afterEach(cleanup)` needed (Vitest lacks globals)

### File List

- `frontend/src/shared/types/user.ts` (new)
- `frontend/src/shared/types/api.ts` (new)
- `frontend/src/shared/lib/apiClient.ts` (new)
- `frontend/src/shared/lib/queryClient.ts` (new)
- `frontend/src/shared/components/LoadingSpinner.tsx` (new)
- `frontend/src/shared/components/ErrorMessage.tsx` (new)
- `frontend/src/shared/hooks/useCurrentUser.ts` (new)
- `frontend/src/features/auth/useAuth.ts` (new — primary)
- `frontend/src/features/auth/LoginPage.tsx` (new)
- `frontend/src/features/auth/LoginPage.test.tsx` (new)
- `frontend/src/hooks/useAuth.ts` (modified — re-export)
- `frontend/src/main.tsx` (modified)
- `frontend/src/routes/_layout.tsx` (modified)
- `frontend/src/routes/login.tsx` (modified — thin wrapper)
- `frontend/src/routes/_layout/admin.tsx` (modified)
- `frontend/src/components/Sidebar/AppSidebar.tsx` (modified)
- `frontend/src/routes/_layout/settings.tsx` (modified)
