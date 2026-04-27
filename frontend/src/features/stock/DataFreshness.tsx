import type { StockScoreResponse } from "@/shared/types/stock"

function fmt(iso: string): string {
  return new Date(iso).toUTCString().replace(" GMT", " UTC")
}

interface Props {
  data: StockScoreResponse
}

export function DataFreshness({ data }: Props) {
  return (
    <div className="rounded-lg border bg-card p-4">
      <p className="text-xs text-muted-foreground uppercase tracking-wider mb-3">Data Freshness</p>
      <div className="grid gap-1.5 text-xs">
        <Row label="Kite data as of" value={fmt(data.kite_snapshot_ts)} />
        <Row label="Screener CSV" value={fmt(data.screener_csv_ts)} />
        <Row label="RBI CSV" value={fmt(data.rbi_csv_ts)} />
        <Row label="Score computed" value={fmt(data.computation_timestamp)} />
      </div>
    </div>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-4">
      <span className="text-muted-foreground shrink-0">{label}:</span>
      <span className="font-mono text-right">{value}</span>
    </div>
  )
}
