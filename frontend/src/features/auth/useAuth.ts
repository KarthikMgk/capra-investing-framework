import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { type UserRegister, UsersService } from "@/client"
import apiClient from "@/shared/lib/apiClient"
import type { User } from "@/shared/types/user"

export const currentUserQueryOptions = {
  queryKey: ["currentUser"] as const,
  queryFn: () => apiClient.get<User>("/api/v1/auth/me").then((r) => r.data),
  retry: false,
  staleTime: 5 * 60 * 1000,
}

export function useCurrentUser() {
  return useQuery(currentUserQueryOptions)
}

export function useLogin() {
  const navigate = useNavigate()
  const qc = useQueryClient()

  return useMutation({
    mutationFn: (credentials: { email: string; password: string }) =>
      apiClient.post("/api/v1/auth/login", credentials),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["currentUser"] })
      navigate({ to: "/" })
    },
  })
}

export function useLogout() {
  const navigate = useNavigate()
  const qc = useQueryClient()

  return useMutation({
    mutationFn: () => apiClient.post("/api/v1/auth/logout"),
    onSuccess: () => {
      qc.clear()
      navigate({ to: "/login" })
    },
  })
}

export function useSignUp() {
  const navigate = useNavigate()

  return useMutation({
    mutationFn: (data: UserRegister) =>
      UsersService.registerUser({ requestBody: data }),
    onSuccess: () => {
      navigate({ to: "/login" })
    },
  })
}

const useAuth = () => {
  const { data: user } = useCurrentUser()
  const loginMutation = useLogin()
  const logoutMutation = useLogout()
  const signUpMutation = useSignUp()

  const logout = () => logoutMutation.mutate()

  return { user, loginMutation, signUpMutation, logout }
}

export default useAuth
