export { default, useCurrentUser, useLogin, useLogout } from "@/features/auth/useAuth"

// Kept for template routes (signup, recover-password, reset-password) that are
// pending removal. Always returns false since auth state lives in httpOnly cookies.
export const isLoggedIn = () => false
