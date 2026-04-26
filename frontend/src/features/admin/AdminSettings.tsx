import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { LoadingButton } from "@/components/ui/loading-button"
import { PasswordInput } from "@/components/ui/password-input"
import { ErrorMessage } from "@/shared/components/ErrorMessage"
import { LoadingSpinner } from "@/shared/components/LoadingSpinner"
import type { ApiError } from "@/shared/types/api"
import apiClient from "@/shared/lib/apiClient"
import type { AxiosError } from "axios"

interface KiteCredentialsStatus {
  api_key_set: boolean
  access_token_set: boolean
  updated_at: string | null
}

const formSchema = z.object({
  api_key: z.string().min(1, { message: "API Key is required" }),
  access_token: z.string().min(1, { message: "Access Token is required" }),
})

type FormData = z.infer<typeof formSchema>

function StatusBadge({ set }: { set: boolean }) {
  return set ? (
    <span className="text-sm font-medium text-green-600">SET</span>
  ) : (
    <span className="text-sm font-medium text-muted-foreground">NOT SET</span>
  )
}

export function AdminSettings() {
  const qc = useQueryClient()

  const { data: status, isLoading } = useQuery<KiteCredentialsStatus>({
    queryKey: ["kiteSettings"],
    queryFn: () =>
      apiClient
        .get<KiteCredentialsStatus>("/api/v1/settings/kite")
        .then((r) => r.data),
  })

  const mutation = useMutation({
    mutationFn: (data: FormData) =>
      apiClient.put("/api/v1/settings/kite", data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["kiteSettings"] })
    },
  })

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: { api_key: "", access_token: "" },
  })

  const onSubmit = (data: FormData) => {
    if (mutation.isPending) return
    mutation.mutate(data)
  }

  const errorMessage = mutation.isError
    ? ((mutation.error as AxiosError<ApiError>)?.response?.data?.error
        ?.message ?? "Failed to save credentials. Please try again.")
    : null

  return (
    <div className="max-w-md flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Kite Connect Settings</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Store your Kite Connect API credentials. Values are encrypted at rest.
        </p>
      </div>

      {isLoading ? (
        <LoadingSpinner />
      ) : (
        <div className="flex gap-6 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">API Key:</span>
            <StatusBadge set={status?.api_key_set ?? false} />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">Access Token:</span>
            <StatusBadge set={status?.access_token_set ?? false} />
          </div>
        </div>
      )}

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="flex flex-col gap-4">
          <FormField
            control={form.control}
            name="api_key"
            render={({ field }) => (
              <FormItem>
                <FormLabel>API Key</FormLabel>
                <FormControl>
                  <PasswordInput placeholder="Kite Connect API Key" {...field} />
                </FormControl>
                <FormMessage className="text-xs" />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="access_token"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Access Token</FormLabel>
                <FormControl>
                  <PasswordInput placeholder="Kite Connect Access Token" {...field} />
                </FormControl>
                <FormMessage className="text-xs" />
              </FormItem>
            )}
          />

          {errorMessage && <ErrorMessage message={errorMessage} />}

          {mutation.isSuccess && (
            <p className="text-sm text-green-600">Credentials saved successfully.</p>
          )}

          <div className="flex gap-3">
            <LoadingButton type="submit" loading={mutation.isPending}>
              Save Credentials
            </LoadingButton>
            {form.formState.isDirty && (
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  form.reset()
                  mutation.reset()
                }}
              >
                Cancel
              </Button>
            )}
          </div>
        </form>
      </Form>
    </div>
  )
}
