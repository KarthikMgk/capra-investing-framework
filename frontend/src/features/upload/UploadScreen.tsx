import { useState } from "react"
import { LoadingButton } from "@/components/ui/loading-button"
import { FileDropZone } from "./FileDropZone"
import { useUploadRbi, useUploadScreener } from "./useUpload"
import { ValidationResult } from "./ValidationResult"

interface UploadSectionProps {
  label: string
  uploadHook: typeof useUploadScreener
}

function UploadSection({ label, uploadHook }: UploadSectionProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const mutation = uploadHook()

  const status = mutation.isPending
    ? "loading"
    : mutation.isSuccess
      ? "success"
      : mutation.isError
        ? "error"
        : "idle"

  return (
    <div className="flex flex-col gap-4 rounded-lg border p-6">
      <h2 className="text-lg font-semibold">{label}</h2>

      <FileDropZone
        label={label}
        onFileSelected={setSelectedFile}
        disabled={mutation.isPending}
      />

      <LoadingButton
        disabled={!selectedFile || mutation.isPending}
        loading={mutation.isPending}
        onClick={() => selectedFile && mutation.mutate(selectedFile)}
      >
        Upload
      </LoadingButton>

      <ValidationResult
        status={status}
        data={mutation.data}
        error={mutation.error}
      />
    </div>
  )
}

export function UploadScreen() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">CSV Data Upload</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Upload Screener.in and RBI macro data files to refresh the computation engine.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <UploadSection label="Screener.in Data" uploadHook={useUploadScreener} />
        <UploadSection label="RBI Macro Data" uploadHook={useUploadRbi} />
      </div>
    </div>
  )
}
