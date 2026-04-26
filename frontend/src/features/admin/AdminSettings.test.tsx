import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { cleanup, render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { AdminSettings } from "./AdminSettings"

vi.mock("@/shared/lib/apiClient", () => ({
  default: {
    get: vi.fn(),
    put: vi.fn(),
  },
}))

import apiClient from "@/shared/lib/apiClient"

function wrapper() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  )
}

afterEach(cleanup)

beforeEach(() => {
  vi.clearAllMocks()
})

describe("AdminSettings", () => {
  it("renders status indicators and form fields", async () => {
    vi.mocked(apiClient.get).mockResolvedValue({
      data: { api_key_set: true, access_token_set: false, updated_at: null },
    })

    render(<AdminSettings />, { wrapper: wrapper() })

    await waitFor(() => {
      expect(screen.getByText("SET")).toBeInTheDocument()
      expect(screen.getByText("NOT SET")).toBeInTheDocument()
    })

    expect(screen.getByLabelText("API Key")).toBeInTheDocument()
    expect(screen.getByLabelText("Access Token")).toBeInTheDocument()
    expect(
      screen.getByRole("button", { name: /save credentials/i }),
    ).toBeInTheDocument()
  })

  it("calls PUT with form values on submit", async () => {
    vi.mocked(apiClient.get).mockResolvedValue({
      data: { api_key_set: false, access_token_set: false, updated_at: null },
    })
    vi.mocked(apiClient.put).mockResolvedValue({ data: { status: "ok" } })

    const user = userEvent.setup()
    render(<AdminSettings />, { wrapper: wrapper() })

    await waitFor(() =>
      expect(screen.getByLabelText("API Key")).toBeInTheDocument(),
    )

    await user.type(screen.getByLabelText("API Key"), "my-api-key")
    await user.type(screen.getByLabelText("Access Token"), "my-access-token")
    await user.click(screen.getByRole("button", { name: /save credentials/i }))

    await waitFor(() => {
      expect(apiClient.put).toHaveBeenCalledWith("/api/v1/settings/kite", {
        api_key: "my-api-key",
        access_token: "my-access-token",
      })
    })
  })

  it("shows inline success message after successful save", async () => {
    vi.mocked(apiClient.get).mockResolvedValue({
      data: { api_key_set: false, access_token_set: false, updated_at: null },
    })
    vi.mocked(apiClient.put).mockResolvedValue({ data: { status: "ok" } })

    const user = userEvent.setup()
    render(<AdminSettings />, { wrapper: wrapper() })

    await waitFor(() =>
      expect(screen.getByLabelText("API Key")).toBeInTheDocument(),
    )

    await user.type(screen.getByLabelText("API Key"), "key")
    await user.type(screen.getByLabelText("Access Token"), "token")
    await user.click(screen.getByRole("button", { name: /save credentials/i }))

    await waitFor(() => {
      expect(
        screen.getByText(/credentials saved successfully/i),
      ).toBeInTheDocument()
    })
  })

  it("shows inline error message when save fails", async () => {
    vi.mocked(apiClient.get).mockResolvedValue({
      data: { api_key_set: false, access_token_set: false, updated_at: null },
    })
    vi.mocked(apiClient.put).mockRejectedValue({
      response: {
        data: { error: { message: "Encryption key misconfigured." } },
      },
    })

    const user = userEvent.setup()
    render(<AdminSettings />, { wrapper: wrapper() })

    await waitFor(() =>
      expect(screen.getByLabelText("API Key")).toBeInTheDocument(),
    )

    await user.type(screen.getByLabelText("API Key"), "key")
    await user.type(screen.getByLabelText("Access Token"), "token")
    await user.click(screen.getByRole("button", { name: /save credentials/i }))

    await waitFor(() => {
      expect(
        screen.getByText("Encryption key misconfigured."),
      ).toBeInTheDocument()
    })
  })
})
