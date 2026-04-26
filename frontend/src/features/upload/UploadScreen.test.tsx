import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { UploadScreen } from "./UploadScreen"

vi.mock("@/shared/lib/apiClient", () => ({
  default: { post: vi.fn() },
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
beforeEach(() => vi.clearAllMocks())

const csvFile = new File(["Symbol,Name\nTEST,Corp"], "data.csv", { type: "text/csv" })
const xlsxFile = new File(["binary"], "data.xlsx", {
  type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
})

describe("UploadScreen", () => {
  // AC2: non-CSV file dropped shows inline error, no API call
  it("shows error when non-CSV file is dropped on Screener zone", () => {
    render(<UploadScreen />, { wrapper: wrapper() })

    const dropZones = screen.getAllByTestId("drop-zone")
    const screenerZone = dropZones[0]

    fireEvent.drop(screenerZone, {
      dataTransfer: { files: [xlsxFile] },
    })

    expect(screen.getByTestId("drop-zone-error")).toHaveTextContent(
      "Only .csv files are accepted",
    )
    expect(apiClient.post).not.toHaveBeenCalled()
  })

  // AC5: valid CSV + successful upload shows success with batch_id
  it("shows success message with batch_id after successful screener upload", async () => {
    vi.mocked(apiClient.post).mockResolvedValue({
      data: { status: "ok", batch_id: "abc-123-def" },
    })

    const user = userEvent.setup()
    render(<UploadScreen />, { wrapper: wrapper() })

    const fileInputs = screen.getAllByTestId("file-input")
    await user.upload(fileInputs[0], csvFile)

    const uploadButtons = screen.getAllByRole("button", { name: /upload/i })
    await user.click(uploadButtons[0])

    await waitFor(() => {
      expect(screen.getByTestId("upload-success")).toHaveTextContent(
        "Batch ID: abc-123-def",
      )
    })
  })

  // AC6: API returns 400 with column details → shows specific column error
  it("shows column-level error details on CSV_COLUMN_MISSING response", async () => {
    vi.mocked(apiClient.post).mockRejectedValue({
      response: {
        data: {
          error: {
            code: "CSV_COLUMN_MISSING",
            message: "Required columns are missing.",
            details: { expected: ["PE", "PB"], found: ["pe", "pb"] },
          },
        },
      },
    })

    const user = userEvent.setup()
    render(<UploadScreen />, { wrapper: wrapper() })

    const fileInputs = screen.getAllByTestId("file-input")
    await user.upload(fileInputs[0], csvFile)

    const uploadButtons = screen.getAllByRole("button", { name: /upload/i })
    await user.click(uploadButtons[0])

    await waitFor(() => {
      const errorBlock = screen.getByTestId("upload-column-error")
      expect(errorBlock).toHaveTextContent("PE")
      expect(errorBlock).toHaveTextContent("pe")
    })
  })

  // AC1: both sections are rendered independently
  it("renders two independent upload sections", () => {
    render(<UploadScreen />, { wrapper: wrapper() })
    expect(screen.getByText("Screener.in Data")).toBeInTheDocument()
    expect(screen.getByText("RBI Macro Data")).toBeInTheDocument()
    expect(screen.getAllByTestId("drop-zone")).toHaveLength(2)
  })
})
