import { useRef, useState } from "react"

interface FileDropZoneProps {
  onFileSelected: (file: File) => void
  disabled?: boolean
  label: string
}

export function FileDropZone({ onFileSelected, disabled, label }: FileDropZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const [selectedName, setSelectedName] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  function handleFile(file: File) {
    if (!file.name.endsWith(".csv") && file.type !== "text/csv") {
      setError("Only .csv files are accepted")
      setSelectedName(null)
      return
    }
    setError(null)
    setSelectedName(file.name)
    onFileSelected(file)
  }

  return (
    <div className="flex flex-col gap-2">
      <div
        data-testid="drop-zone"
        onClick={() => !disabled && inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setIsDragOver(true) }}
        onDragEnter={(e) => { e.preventDefault(); setIsDragOver(true) }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={(e) => {
          e.preventDefault()
          setIsDragOver(false)
          if (disabled) return
          const file = e.dataTransfer.files[0]
          if (file) handleFile(file)
        }}
        className={[
          "flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed p-8 cursor-pointer transition-colors",
          isDragOver ? "border-blue-500 bg-blue-50 dark:bg-blue-950" : "border-muted-foreground/30",
          disabled ? "opacity-50 cursor-not-allowed" : "hover:border-muted-foreground/60",
        ].join(" ")}
      >
        <p className="text-sm text-muted-foreground">
          {selectedName ?? `Drop a ${label} CSV here, or click to select`}
        </p>
        <input
          ref={inputRef}
          data-testid="file-input"
          type="file"
          accept=".csv"
          className="hidden"
          disabled={disabled}
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) handleFile(file)
            e.target.value = ""
          }}
        />
      </div>
      {error && (
        <p data-testid="drop-zone-error" className="text-sm text-red-600">
          {error}
        </p>
      )}
    </div>
  )
}
