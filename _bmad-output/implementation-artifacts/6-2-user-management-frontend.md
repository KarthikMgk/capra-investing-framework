# Story 6.2: User Management Frontend

Status: ready-for-dev

## Story

As an admin user,
I want a UI screen to view, create, and deactivate user accounts,
so that I can manage who has access to the application without interacting with the database directly.

## Acceptance Criteria

1. **Given** an admin user visits `/admin/users`, **When** the page renders, **Then** a table is displayed listing all users with columns: `email`, `role`, status (`Active`/`Inactive`), and `created_at` (formatted as human-readable date).

2. **Given** the user list is loading, **When** `useUsers` is in-flight, **Then** a `LoadingSpinner` is shown and no partial table content is rendered.

3. **Given** the `GET /api/v1/users` fetch fails, **When** the error state is reached, **Then** an inline `ErrorMessage` is displayed in the table area — not a page-level redirect.

4. **Given** an admin user clicks "Add User", **When** the button is clicked, **Then** a `UserForm` is rendered with fields for `email`, `password`, and a role selector restricted to "Admin" or "Viewer" (dropdown — no free-form input).

5. **Given** the `UserForm` is submitted with valid data, **When** `POST /api/v1/users` succeeds, **Then** the form clears, and the user list refreshes to show the new user (via `queryClient.invalidateQueries(['users'])`).

6. **Given** the `UserForm` is submitted with an email that already exists, **When** the API returns HTTP 409, **Then** an inline validation error "A user with this email already exists." is displayed on the form — the form does not clear.

7. **Given** an active user row, **When** the admin clicks "Deactivate", **Then** `PATCH /api/v1/users/{id}` is called with `{ "is_active": false }` and the row updates to show `Inactive` status (list refreshes via `invalidateQueries(['users'])`).

8. **Given** an inactive user row, **When** the admin clicks "Activate", **Then** `PATCH /api/v1/users/{id}` is called with `{ "is_active": true }` and the row updates to show `Active` status.

9. **Given** a user row in the table, **When** the admin clicks "Delete", **Then** a confirmation dialog/prompt appears asking the admin to confirm the deletion before any API call is made.

10. **Given** the admin confirms deletion in the dialog, **When** `DELETE /api/v1/users/{id}` succeeds, **Then** the user is removed from the list (via `invalidateQueries(['users'])`).

11. **Given** the currently logged-in admin's own row is rendered in the table, **When** the row is displayed, **Then** the "Delete" button is visually disabled and non-clickable — the admin cannot delete themselves.

12. **Given** a non-admin (Viewer) user navigates to `/admin/users`, **When** the `AdminRoute` guard checks the role, **Then** the user is redirected away (to `/` or a 403 page) — they never see the user management screen.

13. **Given** the role selector in `UserForm`, **When** it is rendered, **Then** only "Admin" and "Viewer" are available as options — no freeform text input is accepted.

## Tasks / Subtasks

- [ ] Task 1: Create `frontend/src/features/admin/useUsers.ts` — TanStack Query hooks for user management (AC: 1, 5, 7, 8, 10)
  - [ ] Define `useUsers()` using `useQuery` with key `['users']`, fetching `GET /api/v1/users` via apiClient
  - [ ] Define `useCreateUser()` using `useMutation` calling `POST /api/v1/users`; on `onSuccess`: call `queryClient.invalidateQueries({ queryKey: ['users'] })`
  - [ ] Define `useUpdateUser()` using `useMutation` calling `PATCH /api/v1/users/{id}`; on `onSuccess`: call `queryClient.invalidateQueries({ queryKey: ['users'] })`
  - [ ] Define `useDeleteUser()` using `useMutation` calling `DELETE /api/v1/users/{id}`; on `onSuccess`: call `queryClient.invalidateQueries({ queryKey: ['users'] })`
  - [ ] Export all four hooks from this module
  - [ ] Do NOT use `useState + useEffect` for server state — TanStack Query only

- [ ] Task 2: Create `frontend/src/features/admin/UserForm.tsx` — create user form (AC: 4, 5, 6, 13)
  - [ ] Render a form with:
    - `email` text input (type="email")
    - `password` input (type="password")
    - `role` dropdown (`<select>`) with exactly two options: `<option value="admin">Admin</option>` and `<option value="viewer">Viewer</option>` — no freeform input
  - [ ] On submit: call `useCreateUser().mutate({ email, password, role })`
  - [ ] Show loading state (disable submit button) while `useCreateUser().isPending === true`
  - [ ] On success (`onSuccess` in mutation): clear all form fields
  - [ ] On error: check `error.response?.data?.error?.code === 'DUPLICATE_EMAIL'` — if so, show inline error "A user with this email already exists." next to the email field; for other errors show a generic inline error message
  - [ ] Do NOT navigate away or show a modal on success — form resets in-place

- [ ] Task 3: Create `frontend/src/features/admin/UserManagement.tsx` — user management screen (AC: 1, 2, 3, 7, 8, 9, 10, 11)
  - [ ] Use `useUsers()` for data, `isLoading`, `isError`
  - [ ] Use `useCurrentUser()` from `shared/hooks/useCurrentUser.ts` to get the logged-in admin's user ID
  - [ ] While `isLoading`: render `<LoadingSpinner />` from `shared/components/LoadingSpinner.tsx`
  - [ ] If `isError`: render inline `<ErrorMessage />` in the table area
  - [ ] Render a table with columns: Email, Role, Status, Created At, Actions
    - Status column: show "Active" if `is_active === true`, "Inactive" if `is_active === false`
    - Created At column: format ISO 8601 timestamp to human-readable (e.g., "17 Apr 2026")
  - [ ] Render an "Add User" button above the table; clicking it shows/hides `<UserForm />` (toggle inline — no modal required; keep it simple)
  - [ ] Per-row Actions column:
    - Active user: "Deactivate" button → calls `useUpdateUser().mutate({ id, is_active: false })`
    - Inactive user: "Activate" button → calls `useUpdateUser().mutate({ id, is_active: true })`
    - "Delete" button: if `user.id === currentUser.id` → visually disabled (e.g., `disabled` attribute + muted styling); otherwise shows confirmation dialog before calling `useDeleteUser().mutate(id)`
  - [ ] Confirmation dialog for delete: use `window.confirm("Are you sure you want to delete this user?")` or an inline confirm UI — must block the delete mutation until confirmed

- [ ] Task 4: Wire `UserManagement` into `App.tsx` at `/admin/users` as an `AdminRoute` (AC: 12)
  - [ ] Import `UserManagement` and wrap with `<AdminRoute>` (defined in `shared/components/AdminRoute.tsx` from Epic 1)
  - [ ] Register route `path="/admin/users"` rendering `<AdminRoute><UserManagement /></AdminRoute>`
  - [ ] Verify `AdminRoute` redirects non-admin users before rendering the component

- [ ] Task 5: Write `frontend/src/features/admin/UserManagement.test.tsx` (AC: 1, 5, 7, 11)
  - [ ] Mock `useUsers` to return a list of test users (mix of active/inactive, including the current user)
  - [ ] Assert the user table renders with all expected columns and rows
  - [ ] Assert "Add User" button toggles `UserForm` visibility
  - [ ] Mock `useCreateUser` and assert `UserForm` submission calls the mutation with correct payload
  - [ ] Assert "Deactivate" button calls `useUpdateUser` with `{ is_active: false }` for the correct user ID
  - [ ] Assert the current user's own "Delete" button is disabled (not clickable)
  - [ ] Assert clicking a non-self "Delete" button triggers a confirmation before the mutation fires

## Dev Notes

- **TanStack Query is mandatory — NEVER use `useState + useEffect`:** All server data in `useUsers.ts` MUST use `useQuery` and `useMutation`. This is an explicit anti-pattern in this codebase.
- **Use `queryClient.invalidateQueries({ queryKey: ['users'] })` in all mutation `onSuccess` callbacks:** Each mutation (`create`, `update`, `delete`) must invalidate the `['users']` query key on success so the table refreshes immediately. Import `queryClient` from `shared/lib/queryClient.ts`.
- **Delete requires confirmation:** Never call the delete mutation without user confirmation. Use `window.confirm(...)` for simplicity. If the confirmation returns `false`, do NOT proceed with the API call.
- **Self-delete button must be disabled:** Use `useCurrentUser()` from `frontend/src/shared/hooks/useCurrentUser.ts` (established in Epic 1) to identify the logged-in user. Compare `user.id === currentUser.id` to determine which row to disable. The button must have the `disabled` HTML attribute AND visual muted styling.
- **Role selector must be a `<select>` with fixed options:** Do NOT use a freeform `<input type="text">` for role. The options must be hardcoded as `<option value="admin">Admin</option>` and `<option value="viewer">Viewer</option>`. Any other value would be rejected by the backend with 422.
- **Inline `UserForm` (no modal required):** Show `UserForm` inline below the "Add User" button when clicked. Toggle visibility with local `useState<boolean>`. A modal is allowed but not required — keep implementation simple.
- **409 error handling in `UserForm`:** The `useCreateUser` mutation will receive the error object from Axios. The error code `DUPLICATE_EMAIL` is at `error.response.data.error.code`. Always check the error code before showing the specific message — fall back to a generic error for other codes.
- **`UserResponse` fields are `snake_case`:** `is_active`, `created_at`, `user_id` — never `isActive`, `createdAt`, `userId`. The backend returns `snake_case` per architecture convention.
- **`AdminRoute` already exists:** `shared/components/AdminRoute.tsx` was implemented in Epic 1. Do NOT re-create it. Import and wrap `UserManagement` with it.
- **`useCurrentUser` already exists:** `shared/hooks/useCurrentUser.ts` was implemented in Epic 1. Do NOT re-create it. Import and use it to identify the logged-in user's ID.
- **`UserManagement.test.tsx` location:** Co-located with the component at `frontend/src/features/admin/UserManagement.test.tsx`. This is the frontend test convention per architecture.md.

### Project Structure Notes

- Files to CREATE:
  - `frontend/src/features/admin/useUsers.ts`
  - `frontend/src/features/admin/UserForm.tsx`
  - `frontend/src/features/admin/UserManagement.tsx`
  - `frontend/src/features/admin/UserManagement.test.tsx`
- Files to MODIFY:
  - `frontend/src/App.tsx` — add `/admin/users` route wrapped in `AdminRoute`

### References

- [Source: architecture.md#Structure Patterns — Frontend Project Organization]
- [Source: architecture.md#Process Patterns — Frontend Loading & Error States]
- [Source: architecture.md#Naming Patterns — TypeScript/React Code Naming]
- [Source: architecture.md#Format Patterns — HTTP Status Codes]
- [Source: architecture.md#Architectural Boundaries — API Boundaries (Admin-only)]
- [Source: epics.md#Epic 6: User Management]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
