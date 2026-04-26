export type UserRole = "admin" | "viewer"

export interface User {
  id: string
  email: string
  role: UserRole
  full_name?: string
}
