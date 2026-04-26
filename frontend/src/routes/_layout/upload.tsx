import { createFileRoute, redirect } from "@tanstack/react-router"

import { UploadScreen } from "@/features/upload/UploadScreen"
import { currentUserQueryOptions } from "@/features/auth/useAuth"
import { queryClient } from "@/shared/lib/queryClient"
import type { User } from "@/shared/types/user"

export const Route = createFileRoute("/_layout/upload")({
  component: UploadScreen,
  beforeLoad: async () => {
    if (!queryClient.getQueryData(currentUserQueryOptions.queryKey)) {
      await queryClient.ensureQueryData(currentUserQueryOptions)
    }
    const user = queryClient.getQueryData<User>(currentUserQueryOptions.queryKey)
    if (!user || user.role !== "admin") {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({
    meta: [{ title: "CSV Upload - Capra Investing" }],
  }),
})
