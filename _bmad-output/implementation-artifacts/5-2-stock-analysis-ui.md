# Story 5.2: Stock Analysis UI

Status: ready-for-dev

## Story

As an authenticated user,
I want a full Decision Cockpit screen where I can search any Nifty 50 stock and view its complete framework output,
so that I can make informed investment decisions using the composite score, signal, position size, factor breakdowns, and data freshness indicators.

## Acceptance Criteria

1. **Given** an authenticated user visits `/stock/:symbol` or navigates from the portfolio view, **When** the page renders, **Then** the `StockAnalysis` screen is shown with the selected stock's data loading from `GET /api/v1/stocks/{stock_symbol}`.

2. **Given** a stock symbol is selected or provided via URL param, **When** data loads successfully, **Then** three pillars are rendered: `ScorePillar`, `SignalPillar`, and `PositionPillar`, each displaying their primary value.

3. **Given** the `ScorePillar` is rendered, **When** data is present, **Then** the composite score is displayed to exactly 4 decimal places (e.g., `0.6125`), and a `SignalBadge` showing the 5-state signal is visible.

4. **Given** the `ScorePillar`'s "Show breakdown" button is clicked, **When** the expandable section opens, **Then** a table of all 9 factors is shown with `name`, `weight`, `raw_value`, `weighted_contribution`, and `signal` columns drawn from `factor_breakdown.factors`.

5. **Given** multiple expandable pillar sections exist, **When** one section is expanded or collapsed, **Then** the other sections remain unchanged in their current open/closed state — they toggle independently.

6. **Given** the `SignalPillar` is rendered, **When** the expandable section is opened, **Then** `roc` value, `asymmetry_index` value, `time_stop_months` value, and a human-readable description of the signal trigger conditions are displayed.

7. **Given** the `PositionPillar` is rendered, **When** the expandable section is opened, **Then** the step-by-step calculation is shown: "Base: {base_pct}% × Conviction: {conviction_multiplier} × Volatility: {volatility_adjustment} = {final_pct}%", plus the risk control reminder text: "Max single stock: 10–15%. Maintain 10–20% cash reserve."

8. **Given** the `DataFreshness` component is rendered, **When** a stock is selected, **Then** all four freshness lines are displayed in human-readable format (e.g., "17 Apr 2026, 10:30 UTC"): "Kite data as of: {kite_snapshot_ts}", "Screener CSV: {screener_csv_ts}", "RBI CSV: {rbi_csv_ts}", and "Score computed: {computation_timestamp}".

9. **Given** `GET /api/v1/stocks/{stock_symbol}` returns HTTP 404 with `SCORE_NOT_FOUND`, **When** the UI processes the error, **Then** the message "No analysis available. Ask admin to run a data refresh." is displayed in place of the pillars.

10. **Given** a user types in the `StockSearch` input, **When** characters are entered, **Then** a typeahead dropdown appears filtered by both `stock_symbol` and `name` matching the input, showing only Nifty 50 stocks.

11. **Given** a user selects a stock from the `StockSearch` dropdown, **When** the selection is made, **Then** the browser navigates to `/stock/{symbol}` and the Decision Cockpit loads data for that symbol.

12. **Given** `StockSearch` is rendered, **When** a user types a value that is not in the Nifty 50 list, **Then** only matching Nifty 50 entries appear — no freeform entry outside the list is accepted.

13. **Given** stock data is being fetched, **When** the request is in-flight, **Then** a `LoadingSpinner` is displayed and no partial pillar content is rendered.

14. **Given** the `/stock/:symbol` route is accessed, **When** the user is unauthenticated, **Then** they are redirected to `/login` by the `ProtectedRoute` wrapper.

15. **Given** the portfolio view row is clicked for a holding, **When** navigation to `/stock/{tradingsymbol}` occurs, **Then** the `:symbol` URL param is picked up by `StockAnalysis` and pre-selects that stock automatically.

16. **Given** all numeric values are displayed, **When** rendered, **Then** scores are shown to 4 decimal places, prices to 2 decimal places, and percentages to 2 decimal places.

## Tasks / Subtasks

- [ ] Task 1: Create `frontend/src/features/stock/useStockScore.ts` — TanStack Query hook (AC: 1, 13)
  - [ ] Use `useQuery` from `@tanstack/react-query` with key `['stock', stockSymbol]`
  - [ ] Fetch `GET /api/v1/stocks/{stock_symbol}` via the Axios `apiClient` instance
  - [ ] Set `enabled: !!stockSymbol` — do not fetch if symbol is empty or undefined
  - [ ] Export `useStockScore(stockSymbol: string)` returning `{ data, isLoading, isError, error }`
  - [ ] Do NOT use `useState + useEffect` — TanStack Query only

- [ ] Task 2: Create `frontend/src/features/stock/StockSearch.tsx` — Nifty 50 typeahead component (AC: 10, 11, 12)
  - [ ] Fetch all stocks from `GET /api/v1/stocks` using `useQuery` with key `['stocks']` and `staleTime: Infinity` (list rarely changes)
  - [ ] Render a controlled text input; on change, filter `stocks.items` by `stock_symbol` or `name` matching the input string (case-insensitive)
  - [ ] Render a dropdown list of matched results below the input
  - [ ] On dropdown item click: navigate to `/stock/{symbol}` using `useNavigate()` from `react-router-dom`
  - [ ] Enforce Nifty 50 only — dropdown shows ONLY items from the API response; no freeform text submission
  - [ ] Close dropdown on selection or outside click (use `onBlur` or a click-outside handler)

- [ ] Task 3: Create `frontend/src/features/stock/ScorePillar.tsx` — composite score pillar (AC: 3, 4, 5)
  - [ ] Accept `data: StockScoreResponse` prop
  - [ ] Display `composite_score` formatted to 4 decimal places with `toFixed(4)`
  - [ ] Display `<SignalBadge signal={data.signal} />` (reuse from `features/portfolio/SignalBadge.tsx`)
  - [ ] Render a toggle button labeled "Show breakdown" / "Hide breakdown"
  - [ ] When expanded, render a table of `data.factor_breakdown.factors` — each row: `name`, `weight`, `raw_value`, `weighted_contribution`, `signal`
  - [ ] Manage expanded/collapsed state with local `useState` — independent of other pillars
  - [ ] Parse `data.factor_breakdown` directly as a JavaScript object — NO re-computation on frontend

- [ ] Task 4: Create `frontend/src/features/stock/SignalPillar.tsx` — signal pillar (AC: 5, 6)
  - [ ] Accept `data: StockScoreResponse` prop
  - [ ] Display the 5-state signal name prominently
  - [ ] Render a toggle button to expand/collapse the detail section
  - [ ] When expanded, display:
    - `roc` value from `factor_breakdown.roc`
    - `asymmetry_index` value from `factor_breakdown.asymmetry_index`
    - `time_stop_months` value from `factor_breakdown.time_stop_months`
    - A human-readable description of which conditions triggered the current signal (derive from the `signal` value using a constants map, e.g., `strong_buy` → "Score above threshold, positive ROC, positive Asymmetry Index")
  - [ ] Manage expanded/collapsed state with local `useState` — independent of other pillars

- [ ] Task 5: Create `frontend/src/features/stock/PositionPillar.tsx` — position size pillar (AC: 5, 7, 16)
  - [ ] Accept `data: StockScoreResponse` prop
  - [ ] Display `factor_breakdown.position_breakdown.final_pct` formatted to 2 decimal places as the primary value (e.g., "87.75%")
  - [ ] Render a toggle button to expand/collapse the detail section
  - [ ] When expanded, display step-by-step calculation: "Base: {base_pct}% × Conviction: {conviction_multiplier} × Volatility: {volatility_adjustment} = {final_pct}%"
  - [ ] Include static risk control reminder text (always shown when expanded): "Max single stock: 10–15%. Maintain 10–20% cash reserve."
  - [ ] Manage expanded/collapsed state with local `useState` — independent of other pillars

- [ ] Task 6: Create `frontend/src/features/stock/DataFreshness.tsx` — data freshness display (AC: 8)
  - [ ] Accept `data: StockScoreResponse` prop
  - [ ] Format all ISO 8601 UTC timestamp strings into human-readable format: "17 Apr 2026, 10:30 UTC"
  - [ ] Display four freshness rows:
    - "Kite data as of: {kite_snapshot_ts formatted}"
    - "Screener CSV: {screener_csv_ts formatted}"
    - "RBI CSV: {rbi_csv_ts formatted}"
    - "Score computed: {computation_timestamp formatted}"
  - [ ] Write a local `formatTimestamp(iso: string): string` utility or import from `shared/lib/formatters.ts` if it exists

- [ ] Task 7: Create `frontend/src/features/stock/StockAnalysis.tsx` — top-level Decision Cockpit screen (AC: 1, 2, 9, 13, 14, 15)
  - [ ] Read `:symbol` URL param using `useParams<{ symbol: string }>()`
  - [ ] Render `<StockSearch />` at the top — pre-populates with the current `symbol` param if provided
  - [ ] Use `useStockScore(symbol)` — `enabled: !!symbol`
  - [ ] While `isLoading`: render `<LoadingSpinner />` from `shared/components/LoadingSpinner.tsx`
  - [ ] If `isError` and error code is `SCORE_NOT_FOUND`: display message "No analysis available. Ask admin to run a data refresh."
  - [ ] If `isError` with any other error: render inline `<ErrorMessage />` from `shared/components/ErrorMessage.tsx`
  - [ ] If `data` is present: render 3-pillar layout — `<ScorePillar>`, `<SignalPillar>`, `<PositionPillar>` — and `<DataFreshness>`
  - [ ] Do NOT render partial pillar content during loading

- [ ] Task 8: Wire `StockAnalysis` into `App.tsx` at `/stock/:symbol` as a `ProtectedRoute` (AC: 14, 15)
  - [ ] Import `StockAnalysis` and wrap with `<ProtectedRoute>`
  - [ ] Register route `path="/stock/:symbol"` rendering `<ProtectedRoute><StockAnalysis /></ProtectedRoute>`
  - [ ] Confirm the `:symbol` param matches what portfolio navigation (`/stock/${tradingsymbol}`) produces — no mismatch

- [ ] Task 9: Write `frontend/src/features/stock/StockAnalysis.test.tsx` (AC: 3, 4, 5, 9, 10, 11)
  - [ ] Mock `useStockScore` to return a full `StockScoreResponse` fixture with all fields
  - [ ] Assert `ScorePillar` renders composite score to 4 decimal places
  - [ ] Assert each pillar's expand/collapse toggle works independently (expand one, verify other two remain collapsed)
  - [ ] Assert `SignalPillar` expanded section shows `roc`, `asymmetry_index`, `time_stop_months`
  - [ ] Assert `PositionPillar` expanded section shows step-by-step calculation and risk reminder text
  - [ ] Mock `useStockScore` returning 404 error with `SCORE_NOT_FOUND`; assert "No analysis available. Ask admin to run a data refresh." message is rendered
  - [ ] Mock `GET /api/v1/stocks` and assert `StockSearch` filters by name and symbol correctly

## Dev Notes

- **TanStack Query is mandatory — NEVER use `useState + useEffect`:** All server data fetching in `useStockScore.ts` and `StockSearch.tsx` MUST use `useQuery`. Using `useState` + `useEffect` for API calls is an explicit anti-pattern in this codebase.
- **Expandable pillar sections toggle independently:** Each pillar manages its own `isExpanded` state with `useState`. Expanding `ScorePillar` must NOT affect `SignalPillar` or `PositionPillar`. Never use shared/global state for expand/collapse.
- **`factor_breakdown` JSONB is pre-structured — parse directly:** The `factor_breakdown` field in the API response is already a structured JavaScript object. Access `response.factor_breakdown.factors`, `response.factor_breakdown.roc`, etc. directly. Do NOT re-compute or re-derive any values on the frontend.
- **Score to 4 decimal places:** Use `score.toFixed(4)`. Prices use `price.toFixed(2)`. Percentages use `pct.toFixed(2)`. Never use raw unformatted numbers in display.
- **"SCORE_NOT_FOUND" user message (exact):** When the API returns 404 with `code: "SCORE_NOT_FOUND"`, the UI MUST display: "No analysis available. Ask admin to run a data refresh." — not a generic error message.
- **`/stock/:symbol` URL param name:** The route parameter is named `:symbol`. Use `useParams<{ symbol: string }>()` to read it. The portfolio view navigates to `/stock/${holding.tradingsymbol}` — both must use the same path shape.
- **`StockSearch` enforces Nifty 50 only:** The dropdown MUST only show stocks from `GET /api/v1/stocks` response. Free-form text that doesn't match a Nifty 50 stock must not trigger a navigation or API call.
- **`StockSearch` `staleTime: Infinity`:** The Nifty 50 list never changes during a session. Set `staleTime: Infinity` on the stocks list query to avoid re-fetching on every mount.
- **Reuse `SignalBadge` from portfolio feature:** `ScorePillar` must import `SignalBadge` from `frontend/src/features/portfolio/SignalBadge.tsx`. Do not create a duplicate component.
- **Detecting `SCORE_NOT_FOUND` in the frontend error handler:** The Axios `apiClient` will receive the 404 response. Check `error.response?.data?.error?.code === 'SCORE_NOT_FOUND'` to distinguish this case from other errors (e.g., 401, 500).
- **Timestamp formatting:** Convert ISO 8601 UTC strings (e.g., `"2026-04-17T10:30:00Z"`) to `"17 Apr 2026, 10:30 UTC"` format. Use `new Date(iso).toUTCString()` or a locale-aware formatter — do not hardcode date format strings.
- **All TypeScript types in `shared/types/stock.ts`:** Define `StockScoreResponse`, `FactorBreakdown`, `FactorItem`, `PositionBreakdown`, `StockListItem` there. Import in component files — do not define types inline in component files.
- **Independent pillar state — anti-pattern to avoid:** Do NOT use a single `expandedPillar: string | null` state variable that only allows one panel open at a time. Each pillar must have its own boolean `isExpanded` state.

### Project Structure Notes

- Files to CREATE:
  - `frontend/src/features/stock/useStockScore.ts`
  - `frontend/src/features/stock/StockSearch.tsx`
  - `frontend/src/features/stock/ScorePillar.tsx`
  - `frontend/src/features/stock/SignalPillar.tsx`
  - `frontend/src/features/stock/PositionPillar.tsx`
  - `frontend/src/features/stock/DataFreshness.tsx`
  - `frontend/src/features/stock/StockAnalysis.tsx`
  - `frontend/src/features/stock/StockAnalysis.test.tsx`
- Files to MODIFY:
  - `frontend/src/App.tsx` — add `/stock/:symbol` route wrapped in `ProtectedRoute`
  - `frontend/src/shared/types/stock.ts` — add `StockScoreResponse`, `StockListItem`, `FactorBreakdown`, `FactorItem`, `PositionBreakdown`

### References

- [Source: architecture.md#Structure Patterns — Frontend Project Organization]
- [Source: architecture.md#Format Patterns — Numeric Precision]
- [Source: architecture.md#Format Patterns — Date/Time Format]
- [Source: architecture.md#Process Patterns — Frontend Loading & Error States]
- [Source: architecture.md#Gap Analysis & Resolutions — Gap 1 (factor_breakdown JSONB Schema)]
- [Source: architecture.md#Naming Patterns — TypeScript/React Code Naming]
- [Source: epics.md#Epic 5: Stock Analysis — Decision Cockpit]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
