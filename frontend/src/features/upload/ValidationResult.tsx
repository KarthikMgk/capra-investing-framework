import type { AxiosError } from "axios"
import { LoadingSpinner } from "@/shared/components/LoadingSpinner"
import type { ApiError } from "@/shared/types/api"
import type { UploadResponse } from "./useUpload"

interface ValidationResultProps {
  status: "idle" | "loading" | "success" | "error"
  data?: UploadResponse
  error?: unknown
}

interface ColumnErrorDetails {
  expected: string[]
  found: string[]
}

export function ValidationResult({ status, data, error }: ValidationResultProps) {
  if (status === "idle") return null

  if (status === "loading") return <LoadingSpinner />

  if (status === "success" && data) {
    return (
      <p data-testid="upload-success" className="text-sm text-green-600">
        Upload successful. Batch ID: {data.batch_id}
      </p>
    )
  }

  if (status === "error") {
    const axiosError = error as AxiosError<ApiError>
    const apiErr = axiosError?.response?.data?.error
    const isColumnError = apiErr?.code === "CSV_COLUMN_MISSING"

    if (isColumnError && apiErr?.details) {
      const details = apiErr.details as ColumnErrorDetails
      const missing = details.expected?.filter(
        (col) => !details.found?.includes(col),
      )
      return (
        <div data-testid="upload-column-error" className="flex flex-col gap-1 text-sm text-red-600">
          <p className="font-medium">Upload failed — missing required columns</p>
          <p>Expected: {details.expected?.join(", ")}</p>
          <p>Found in file: {details.found?.join(", ") || "(none)"}</p>
          {missing?.length > 0 && (
            <ul className="list-disc pl-4">
              {missing.map((col) => (
                <li key={col}>Column &apos;{col}&apos; not found in uploaded file</li>
              ))}
            </ul>
          )}
        </div>
      )
    }

    return (
      <p data-testid="upload-error" className="text-sm text-red-600">
        {apiErr?.message ?? "Upload failed. Please try again."}
      </p>
    )
  }

  return null
}
