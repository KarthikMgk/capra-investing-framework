# Story 4.1: Portfolio View UI

Status: ready-for-dev

## Story

As an authenticated user,
I want to view all my Kite Connect holdings on a single screen with live prices and signal badges,
so that I can quickly assess my portfolio health and navigate to any stock's full analysis.

## Acceptance Criteria

1. **Given** an authenticated user visits `/` (home route), **When** the portfolio data loads, **Then** each holding row displays `tradingsymbol`, `name`, `quantity`, and `last_price` formatted to 2 decimal places.

2. **Given** a holding with a computed signal, **When** the portfolio row renders, **Then** a `SignalBadge` appears with the correct Tailwind color class: `strong_buy` → green, `buy` → light green/teal, `hold` → white/neutral, `sell` → orange, `strong_sell` → red.

3. **Given** a holding with no computed signal (score snapshot not yet run), **When** the portfolio row renders, **Then** the `SignalBadge` renders in a neutral/grey state without crashing.

4. **Given** an authenticated user clicks a holding row, **When** the click event fires, **Then** the browser navigates to `/stock/{tradingsymbol}` using React Router `useNavigate` — not a full page reload.

5. **Given** portfolio data is loading, **When** the fetch is in-flight, **Then** a `LoadingSpinner` component is displayed and no partial data is rendered.

6. **Given** the portfolio fetch fails with a network or server error, **When** the error state is reached, **Then** an inline error message is displayed near the portfolio list (not a full-page redirect) without crashing.

7. **Given** an authenticated user (Admin or Viewer), **When** the portfolio page renders, **Then** a "Refresh Data" button is visible regardless of role — role enforcement is handled by the backend.

8. **Given** an authenticated user clicks "Refresh Data", **When** the `POST /api/v1/refresh` mutation succeeds, **Then** `queryClient.invalidateQueries()` is called to refresh all cached data, and the button shows a loading state during the request.

9. **Given** the portfolio route is accessed, **When** the user is unauthenticated, **Then** they are redirected to `/login` by the `ProtectedRoute` wrapper.

10. **Given** `GET /api/v1/portfolio` is called from the frontend, **When** the request is made, **Then** the response includes `{ items: [...], total: int }` and each item has `tradingsymbol`, `name`, `quantity`, `last_price`, `signal`, `signal_color` fields.

11. **Given** the portfolio page renders with holdings, **When** the page is fully loaded after mounting, **Then** it completes within 2 seconds (NFR1).

## Tasks / Subtasks

- [ ] Task 1: Create `backend/app/api/v1/portfolio.py` — `GET /api/v1/portfolio` endpoint (AC: 1, 2, 3, 10)
  - [ ] Define `GET /api/v1/portfolio` with `Depends(get_current_user)` — returns 401 for unauthenticated requests
  - [ ] Call `kite_client.get_holdings()` to fetch live Kite Connect holdings data
  - [ ] For each holding, query `score_snapshots WHERE stock_symbol = ? ORDER BY computation_timestamp DESC LIMIT 1` to get latest signal (LEFT JOIN semantics — symbol with no snapshot returns `signal=None`)
  - [ ] Build and return `PortfolioResponse { items: list[HoldingWithSignal], total: int }`
  - [ ] `HoldingWithSignal` fields: `tradingsymbol: str`, `name: str`, `quantity: int`, `last_price: float`, `signal: str | None`, `signal_color: str | None` (Tailwind class or hex for 5-state map)
  - [ ] Register the portfolio router in `backend/app/main.py` (or `backend/app/api/v1/__init__.py`)

- [ ] Task 2: Create `backend/app/schemas/portfolio.py` — Pydantic schemas (AC: 10)
  - [ ] Define `HoldingWithSignal` Pydantic model with all fields listed above
  - [ ] Define `PortfolioResponse { items: list[HoldingWithSignal], total: int }`
  - [ ] All field names must be `snake_case`

- [ ] Task 3: Create `frontend/src/features/portfolio/usePortfolio.ts` — TanStack Query hook (AC: 5, 6, 11)
  - [ ] Use `useQuery` from `@tanstack/react-query` with key `['portfolio']`
  - [ ] Fetch `GET /api/v1/portfolio` via the Axios `apiClient` instance
  - [ ] Set `staleTime: 0` so live prices are always fresh on mount — never served from stale cache
  - [ ] Export `usePortfolio()` returning `{ data, isLoading, isError, error }`

- [ ] Task 4: Create `frontend/src/features/portfolio/SignalBadge.tsx` — 5-state signal badge component (AC: 2, 3)
  - [ ] Accept `signal: string | null | undefined` prop
  - [ ] Map signal value to Tailwind CSS background color class:
    - `strong_buy` → `bg-green-600 text-white`
    - `buy` → `bg-teal-400 text-white`
    - `hold` → `bg-white text-gray-700 border border-gray-300`
    - `sell` → `bg-orange-500 text-white`
    - `strong_sell` → `bg-red-600 text-white`
    - `null` / unknown → `bg-gray-300 text-gray-600`
  - [ ] Render as a small badge `<span>` with the signal label (or "—" if null)
  - [ ] Use only Tailwind CSS classes — no inline style attributes

- [ ] Task 5: Create `frontend/src/features/portfolio/PortfolioRow.tsx` — single holding row (AC: 1, 2, 3, 4)
  - [ ] Accept `holding: HoldingWithSignal` prop
  - [ ] Render `tradingsymbol`, `name`, `quantity`, `last_price` (formatted to 2 decimal places with `toFixed(2)`)
  - [ ] Render `<SignalBadge signal={holding.signal} />`
  - [ ] Entire row is clickable — use `useNavigate()` from `react-router-dom` to navigate to `/stock/${holding.tradingsymbol}` on click
  - [ ] Do NOT use `<a href>` — use `useNavigate` only

- [ ] Task 6: Create `frontend/src/shared/hooks/useRefresh.ts` — refresh mutation hook (AC: 7, 8)
  - [ ] Use `useMutation` from `@tanstack/react-query` calling `POST /api/v1/refresh` via apiClient
  - [ ] On `onSuccess`: call `queryClient.invalidateQueries()` (no key filter — invalidates all queries)
  - [ ] Export `useRefresh()` returning `{ mutate, isPending }` so caller can show loading state on button
  - [ ] Do NOT create the `/api/v1/refresh` backend endpoint in this story — it is implemented in Epic 3

- [ ] Task 7: Create `frontend/src/features/portfolio/PortfolioView.tsx` — top-level portfolio screen (AC: 1, 2, 3, 4, 5, 6, 7, 8)
  - [ ] Use `usePortfolio()` for data, `isLoading`, `isError`
  - [ ] While `isLoading`: render `<LoadingSpinner />` from `shared/components/LoadingSpinner.tsx`
  - [ ] If `isError`: render inline `<ErrorMessage />` near the list area — do not full-page redirect
  - [ ] Render a list of `<PortfolioRow>` for each item in `data.items`
  - [ ] Render a "Refresh Data" button that calls `refresh.mutate()` from `useRefresh()`; button shows loading indicator while `refresh.isPending === true`; button is visible to ALL authenticated users

- [ ] Task 8: Wire `PortfolioView` into `App.tsx` at `/` as a `ProtectedRoute` (AC: 9)
  - [ ] Import `PortfolioView` and wrap with `<ProtectedRoute>` (defined in `shared/components/ProtectedRoute.tsx` from Epic 1)
  - [ ] Register route `path="/"` rendering `<ProtectedRoute><PortfolioView /></ProtectedRoute>`
  - [ ] Verify the route is the default home route for authenticated users

- [ ] Task 9: Write `frontend/src/features/portfolio/PortfolioView.test.tsx` (AC: 1, 2, 4, 7, 8)
  - [ ] Mock `usePortfolio` to return a list of test holdings
  - [ ] Assert holding rows render with correct symbol, name, quantity, and formatted price
  - [ ] Assert `SignalBadge` displays for each holding with correct content
  - [ ] Assert clicking a row navigates to `/stock/{tradingsymbol}` (verify with mock router)
  - [ ] Assert "Refresh Data" button is present in the rendered output
  - [ ] Assert clicking "Refresh Data" calls the refresh mutation

## Dev Notes

- **TanStack Query is mandatory — NEVER use `useState + useEffect + fetch`:** All server state in `usePortfolio.ts` MUST use `useQuery`. Using local state with `useEffect` for API calls is an explicit anti-pattern in this codebase.
- **`staleTime: 0` on portfolio query:** Live prices must be fresh on each component mount. Do not set any positive `staleTime` value on the portfolio query — it would serve stale Kite prices.
- **Signal badge colors with Tailwind only:** All color styling on `SignalBadge` MUST use Tailwind CSS class strings. Do not use inline `style={{ backgroundColor: '...' }}`. This is required for Tailwind v4's purge step to retain the color classes in the production bundle.
- **Navigation to stock analysis uses `useNavigate` only:** Do NOT use `<a href="/stock/...">`. The entire portfolio row is clickable and must use React Router's `useNavigate` hook to avoid full page reloads.
- **"Refresh Data" button visible to ALL authenticated users:** Both Admin and Viewer users must see the button. FR18/FR19 enforcement (viewer gets 403) is handled by the backend `POST /api/v1/refresh` endpoint. The frontend does NOT conditionally hide this button based on role.
- **`useRefresh` calls `queryClient.invalidateQueries()` with no filter:** On refresh success, call `queryClient.invalidateQueries()` without a key argument to invalidate all cached queries (portfolio, stock scores, etc.) simultaneously.
- **Do NOT implement `POST /api/v1/refresh` backend in this story:** That endpoint is part of Epic 3 (Story 3.x). The `useRefresh` hook must be implemented to call it, but the backend route itself is not in scope for this story.
- **`HoldingWithSignal.signal` is nullable:** Some holdings may not have a computed score yet. The `GET /api/v1/portfolio` endpoint performs a LEFT JOIN with `score_snapshots` — a stock with no snapshot returns `signal: null`. `SignalBadge` must handle `null` gracefully.
- **`kite_client` is a pre-existing service:** `kite_client.get_holdings()` is implemented in Epic 3 (`backend/app/services/kite_client.py`). Import and call it — do not re-implement.
- **`get_current_user` dependency:** Import from `backend/app/api/v1/dependencies.py` (established in Epic 1). Use as `Depends(get_current_user)` on the route.
- **Error response shape:** All backend errors must follow `{"error": {"code": "...", "message": "..."}}`. The portfolio endpoint should raise a `KiteAPIError` (from `core/exceptions.py`) if Kite Connect call fails; the router converts it to HTTP 503 or 500 with the standard envelope.
- **All JSON fields `snake_case`:** `tradingsymbol`, `last_price`, `signal_color` — never `tradingSymbol`, `lastPrice`, `signalColor`.

### Project Structure Notes

- Files to CREATE:
  - `backend/app/api/v1/portfolio.py`
  - `backend/app/schemas/portfolio.py`
  - `frontend/src/features/portfolio/usePortfolio.ts`
  - `frontend/src/features/portfolio/SignalBadge.tsx`
  - `frontend/src/features/portfolio/PortfolioRow.tsx`
  - `frontend/src/features/portfolio/PortfolioView.tsx`
  - `frontend/src/features/portfolio/PortfolioView.test.tsx`
  - `frontend/src/shared/hooks/useRefresh.ts`
- Files to MODIFY:
  - `backend/app/main.py` or `backend/app/api/v1/__init__.py` — register portfolio router
  - `frontend/src/App.tsx` — add `/` route wrapped in `ProtectedRoute`

### References

- [Source: architecture.md#Structure Patterns — Backend Project Organization]
- [Source: architecture.md#Structure Patterns — Frontend Project Organization]
- [Source: architecture.md#Format Patterns — API Response Formats]
- [Source: architecture.md#Process Patterns — Frontend Loading & Error States]
- [Source: architecture.md#Naming Patterns — JSON Field Naming Critical Rule]
- [Source: architecture.md#Data Architecture — Score Cache & Audit Trail]
- [Source: epics.md#Epic 4: Portfolio View]
- [Source: epics.md#Additional Requirements — Axios withCredentials: true]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
