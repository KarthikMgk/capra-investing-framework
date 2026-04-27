import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute, Outlet, redirect, useMatches } from "@tanstack/react-router"
import { Suspense } from "react"

import { type UserPublic, UsersService } from "@/client"
import AddUser from "@/components/Admin/AddUser"
import { columns, type UserTableData } from "@/components/Admin/columns"
import { DataTable } from "@/components/Common/DataTable"
import PendingUsers from "@/components/Pending/PendingUsers"
import { currentUserQueryOptions } from "@/features/auth/useAuth"
import useAuth from "@/hooks/useAuth"
import { queryClient } from "@/shared/lib/queryClient"
import type { User } from "@/shared/types/user"

function getUsersQueryOptions() {
  return {
    queryFn: () => UsersService.readUsers({ skip: 0, limit: 100 }),
    queryKey: ["users"],
  }
}

export const Route = createFileRoute("/_layout/admin")({
  component: Admin,
  beforeLoad: async () => {
    const user = queryClient.getQueryData<User>(currentUserQueryOptions.queryKey)
    if (!user) {
      await queryClient.ensureQueryData(currentUserQueryOptions)
    }
    const currentUser = queryClient.getQueryData<User>(
      currentUserQueryOptions.queryKey,
    )
    if (!currentUser || currentUser.role !== "admin") {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({
    meta: [
      {
        title: "Admin - Capra Investing",
      },
    ],
  }),
})

function UsersTableContent() {
  const { user: currentUser } = useAuth()
  const { data: users } = useSuspenseQuery(getUsersQueryOptions())

  const tableData: UserTableData[] = users.data.map((user: UserPublic) => ({
    ...user,
    isCurrentUser: currentUser?.id === user.id,
  }))

  return <DataTable columns={columns} data={tableData} />
}

function UsersTable() {
  return (
    <Suspense fallback={<PendingUsers />}>
      <UsersTableContent />
    </Suspense>
  )
}

function Admin() {
  const matches = useMatches()
  const isChildRoute = matches.some((m) =>
    m.routeId.startsWith("/_layout/admin/"),
  )

  if (isChildRoute) {
    return <Outlet />
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Users</h1>
          <p className="text-muted-foreground">
            Manage user accounts and permissions
          </p>
        </div>
        <AddUser />
      </div>
      <UsersTable />
    </div>
  )
}
