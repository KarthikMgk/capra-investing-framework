# Story 2.2: CSV Upload Frontend

Status: ready-for-dev

## Story

As an admin,
I want a dedicated upload screen where I can drag-and-drop or select Screener.in and RBI macro CSV files and see immediate column-level validation feedback,
so that I know exactly what is wrong with a rejected file and can correct it before re-uploading.

## Acceptance Criteria

1. **Given** an admin navigates to `/upload`, **When** the screen loads, **Then** two independent upload sections are displayed — one for Screener.in data and one for RBI Macro data — each with its own file input, upload button, and status area.

2. **Given** a user drags a non-CSV file (e.g. `.xlsx`) onto either drop zone, **When** the drop is processed, **Then** an inline error message appears ("Only .csv files are accepted") and no upload is initiated.

3. **Given** an admin selects or drops a valid `.csv` file in either drop zone, **When** the file is selected, **Then** the filename is displayed in the drop zone and the upload button becomes enabled.

4. **Given** an admin clicks the upload button after selecting a file, **When** the upload is in progress, **Then** a spinner or loading indicator is shown within the upload section — the rest of the page remains interactive.

5. **Given** the upload API returns a success response (`HTTP 201`), **When** it is received, **Then** a green success message is shown inline in the relevant upload section including the batch_id, and the last upload timestamp updates.

6. **Given** the upload API returns a 400 error with column details, **When** the error is received, **Then** the `ValidationResult` component renders each column error clearly — e.g. "Column 'PE' is missing — found columns: pe, pb, symbol" — not a generic "upload failed" message.

7. **Given** the `useUploadScreener()` mutation, **When** inspected, **Then** it uses TanStack Query `useMutation` — not `useState + fetch` — and sends the file as `multipart/form-data` with the `File` object directly (not base64-encoded).

8. **Given** a viewer (non-admin) navigates to `/upload`, **When** the route guard checks their role, **Then** they see a 403 message or are redirected — the upload UI never renders for viewers.

9. **Given** `UploadScreen.test.tsx` runs, **When** all tests pass, **Then** the suite covers: non-CSV file shows inline error, successful upload shows success with batch_id, API 400 error shows column-level details from `error.details`.

## Tasks / Subtasks

- [ ] Task 1: Create TanStack Query upload mutations (AC: 4, 7)
  - [ ] Create `frontend/src/features/upload/useUpload.ts`
  - [ ] Implement `useUploadScreener()`:
    - Use `useMutation` from `@tanstack/react-query`
    - `mutationFn` accepts a `File` object
    - Build a `FormData` instance: `formData.append("file", file)` — do NOT convert to base64
    - POST to `/api/v1/upload/screener` using `apiClient.post(..., formData, { headers: { "Content-Type": "multipart/form-data" } })` (or omit Content-Type header and let Axios set it with boundary automatically)
    - Return the response data (typed as `UploadResponse`)
  - [ ] Implement `useUploadRbi()`: same pattern, POST to `/api/v1/upload/rbi`
  - [ ] Both mutations share the same pattern — extract a shared `createUploadMutation(endpoint: string)` factory if it reduces duplication

- [ ] Task 2: Create FileDropZone component (AC: 2, 3)
  - [ ] Create `frontend/src/features/upload/FileDropZone.tsx`
  - [ ] Props: `onFileSelected: (file: File) => void`, `disabled?: boolean`, `label: string`
  - [ ] Render a styled `<div>` with `onDragOver`, `onDrop`, `onDragEnter`, `onDragLeave` handlers — prevent default on all drag events to enable drop
  - [ ] Render a hidden `<input type="file" accept=".csv">` triggered by clicking the drop zone
  - [ ] On file drop or input change:
    - Check `file.name.endsWith(".csv")` or `file.type === "text/csv"` — if not `.csv`, set local error state and call `onFileSelected` with nothing
    - If `.csv`: clear error state, display filename in the drop zone, call `onFileSelected(file)`
  - [ ] Display inline error message if non-CSV file was dropped: "Only .csv files are accepted"
  - [ ] Visual states: idle (dashed border), drag-over (highlighted border), file-selected (show filename), disabled (muted styles)

- [ ] Task 3: Create ValidationResult component (AC: 5, 6)
  - [ ] Create `frontend/src/features/upload/ValidationResult.tsx`
  - [ ] Props: `status: "idle" | "loading" | "success" | "error"`, `response?: UploadResponse`, `error?: ApiError`, `batchId?: string`
  - [ ] When `status === "loading"`: render a spinner (reuse `LoadingSpinner` from `shared/components/`)
  - [ ] When `status === "success"`: render green success state — "Upload successful. Batch ID: {batch_id}"
  - [ ] When `status === "error"` and `error.error.code === "CSV_COLUMN_MISSING"`:
    - Render a red error heading
    - Render `error.error.details.expected` as "Expected columns: ..."
    - Render `error.error.details.found` as "Found in file: ..."
    - Render each column discrepancy explicitly (e.g. "Column 'PE' not found in uploaded file")
  - [ ] When `status === "error"` with other error codes: render `error.error.message` as a generic error message
  - [ ] When `status === "idle"`: render nothing (or a placeholder)

- [ ] Task 4: Create UploadScreen parent component (AC: 1, 4, 5, 6, 8)
  - [ ] Create `frontend/src/features/upload/UploadScreen.tsx`
  - [ ] Render two independent sections: "Screener.in Data" and "RBI Macro Data"
  - [ ] Each section contains:
    - `<FileDropZone>` wired to its own `useState<File | null>` for the selected file
    - An upload button (disabled when no file selected or mutation is pending)
    - `<ValidationResult>` driven by the mutation state (`isIdle`, `isPending`, `isSuccess`, `isError`, `error`, `data`)
    - A last upload timestamp display if prior upload was successful (`data.batch_id` received)
  - [ ] Use `useUploadScreener()` and `useUploadRbi()` from `useUpload.ts`
  - [ ] On upload button click: call `mutation.mutate(selectedFile)` — do not call the API on file selection
  - [ ] While mutation `isPending`: show spinner inside the relevant section; do NOT disable the other section or the page
  - [ ] The two sections are entirely independent — a pending upload on one does not block the other

- [ ] Task 5: Wire UploadScreen into App.tsx under `/upload` as AdminRoute (AC: 8)
  - [ ] Open `frontend/src/App.tsx` (existing file — add route alongside existing routes, do not recreate)
  - [ ] Add `/upload` as a child route wrapped in `<AdminRoute>` (implemented in Story 1.4)
  - [ ] Import `UploadScreen` and use it as the route element

- [ ] Task 6: Write UploadScreen tests (AC: 9)
  - [ ] Create `frontend/src/features/upload/UploadScreen.test.tsx`
  - [ ] Test: dropping a `.xlsx` file onto the Screener drop zone shows "Only .csv files are accepted" and does not call the mutation
  - [ ] Test: selecting a `.csv` file and clicking upload — mock API returns 201 with `{ status: "ok", batch_id: "abc-123" }` — success message with batch_id appears in the Screener section
  - [ ] Test: selecting a `.csv` file and clicking upload — mock API returns 400 with `{ error: { code: "CSV_COLUMN_MISSING", details: { expected: ["PE"], found: ["pe"] } } }` — the ValidationResult component renders "PE" and "pe" in the error display, not just a generic error
  - [ ] Use Vitest + React Testing Library + MSW (or `vi.fn()` mocks for apiClient)

## Dev Notes

- No prior implementation context — this is an early story in the sprint. Story 2.1 (CSV upload backend) must be complete and returning the correct response shapes before end-to-end testing is possible. Story 1.4 (auth frontend with `AdminRoute`) must be complete for the route guard to function. Frontend components can be built and unit-tested with mocked API responses before 2.1 is merged.

- **Use TanStack Query `useMutation` — do NOT use `useState + fetch`.** The anti-pattern `const [loading, setLoading] = useState(false); const handleUpload = async () => { setLoading(true); await fetch(...); setLoading(false); }` is explicitly prohibited by the architecture. Use `const mutation = useMutation(...)` and drive all state from `mutation.isPending`, `mutation.isSuccess`, `mutation.isError`.

- **File must be sent as `multipart/form-data` with the raw `File` object.** Do NOT convert to base64. The backend expects `UploadFile` (FastAPI multipart). Correct pattern:
  ```typescript
  const formData = new FormData();
  formData.append("file", file);  // file is a File object
  apiClient.post("/api/v1/upload/screener", formData);
  // Do NOT set Content-Type header manually — let Axios/browser set multipart boundary
  ```

- **Validation feedback timing:** The architecture requires validation feedback within 500ms of the user initiating upload (NFR3). The upload button triggers the API call; the 500ms target is from button click to error display. This is satisfied by calling the API on button click and displaying the API's error response immediately when received. Do NOT delay feedback with client-side pre-validation (beyond the `.csv` extension check which is instant).

- **Column error display — must show specifics from `error.details`.** The `ValidationResult` component must read `error.error.details.expected` and `error.error.details.found` and display them explicitly. Example:
  ```
  Upload failed — missing required columns
  Expected: PE, PB, ROE
  Found in file: pe, pb, roe
  ```
  A generic "Upload failed. Please try again." is NOT acceptable when column details are available.

- **Two sections are independent.** The Screener and RBI sections each have their own `FileDropZone`, their own `File` state, their own mutation, and their own `ValidationResult`. State from one section does not affect the other. Do not share file selection state between them.

- **`apiClient` import:** Import from `frontend/src/shared/lib/apiClient.ts` (created in Story 1.4). This instance has `withCredentials: true` already set — do not set it again in the upload hook.

- **TypeScript types to use:**
  - `UploadResponse` — define in `frontend/src/features/upload/useUpload.ts` or `frontend/src/shared/types/api.ts`: `{ status: "ok"; batch_id: string }`
  - `ApiError` — already defined in `frontend/src/shared/types/api.ts` (Story 1.4): `{ error: { code: string; message: string; details?: unknown } }`
  - Cast `error.error.details` to `{ expected: string[]; found: string[] }` when `error.error.code === "CSV_COLUMN_MISSING"`

- **Tailwind v4 styling:** Use utility classes directly. No separate config file. Drag-over state can be toggled with a `useState<boolean>` for `isDragOver` and conditionally apply a Tailwind class like `border-blue-500` vs `border-dashed border-gray-300`.

- **File paths — exact list to create or modify:**
  - `frontend/src/features/upload/useUpload.ts` (new)
  - `frontend/src/features/upload/FileDropZone.tsx` (new)
  - `frontend/src/features/upload/ValidationResult.tsx` (new)
  - `frontend/src/features/upload/UploadScreen.tsx` (new)
  - `frontend/src/features/upload/UploadScreen.test.tsx` (new)
  - `frontend/src/App.tsx` (modify existing — add `/upload` route alongside existing routes)

### Project Structure Notes

- All upload feature files live at `frontend/src/features/upload/` as specified in the architecture structure diagram.
- `FileDropZone.tsx` and `ValidationResult.tsx` are upload-feature-specific components — they do NOT go in `shared/components/` (they are not truly shared across features).
- Test file `UploadScreen.test.tsx` is co-located with `UploadScreen.tsx` — not in a separate `__tests__/` folder.
- `useUpload.ts` is a camelCase `.ts` file (non-component), consistent with the naming convention for hooks.
- The `UploadResponse` type may be defined in `useUpload.ts` for locality, or in `shared/types/api.ts` if the computation engine screen also references it — prefer local definition unless it needs to be shared.

### References

- [Source: architecture.md#Frontend Architecture — Server State Management, HTTP Client]
- [Source: architecture.md#Project Structure & Boundaries — Frontend Project Organization (features/upload/)]
- [Source: architecture.md#Implementation Patterns & Consistency Rules — Frontend Loading & Error States]
- [Source: architecture.md#Implementation Patterns & Consistency Rules — Anti-Patterns (useState + useEffect)]
- [Source: architecture.md#API & Communication Patterns — Error Response Shape]
- [Source: architecture.md#Data Flow — CSV upload (data ingestion loop)]
- [Source: epics.md#Epic 2: CSV Data Upload]
- [Source: epics.md#FR28, FR29, FR30, FR31, FR32, FR33, FR34]
- [Source: epics.md#NFR3: CSV upload validation feedback appears within 500ms]

## Dev Agent Record

### Agent Model Used

_to be filled by dev agent_

### Debug Log References

### Completion Notes List

### File List
