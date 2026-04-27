import { useMutation } from "@tanstack/react-query"
import apiClient from "@/shared/lib/apiClient"
import { queryClient } from "@/shared/lib/queryClient"

export function useRefresh() {
  return useMutation({
    mutationFn: () =>
      apiClient.post("/api/v1/refresh").then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries()
    },
  })
}
