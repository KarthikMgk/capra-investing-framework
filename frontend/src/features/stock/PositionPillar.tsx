import { useState } from "react"
import { ChevronDown, ChevronUp } from "lucide-react"
import { Button } from "@/components/ui/button"
import type { StockScoreResponse } from "@/shared/types/stock"

interface Props {
  data: StockScoreResponse
}

export function PositionPillar({ data }: Props) {
  const [open, setOpen] = useState(false)
  const pb = data.factor_breakdown.position_breakdown

  return (
    <div className="rounded-lg border bg-card p-5 flex flex-col gap-4">
      <div>
        <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Position Size</p>
        <p className="text-4xl font-bold tabular-nums tracking-tight">
          {pb.final_pct.toFixed(2)}%
        </p>
        <p className="text-xs text-muted-foreground mt-1">of base allocation</p>
      </div>

      <Button
        variant="ghost"
        size="sm"
        className="w-fit gap-1.5 text-muted-foreground"
        onClick={() => setOpen((v) => !v)}
      >
        {open ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
        {open ? "Hide" : "Show"} sizing detail
      </Button>

      {open && (
        <div className="flex flex-col gap-4 text-sm">
          <div className="rounded-md bg-muted/50 p-4 font-mono text-sm leading-relaxed">
            <span className="text-muted-foreground">Base </span>
            <span className="font-semibold">{pb.base_pct.toFixed(2)}%</span>
            <span className="text-muted-foreground"> × Conviction </span>
            <span className="font-semibold">{pb.conviction_multiplier}×</span>
            <span className="text-muted-foreground"> × Volatility </span>
            <span className="font-semibold">{pb.volatility_adjustment}×</span>
            <span className="text-muted-foreground"> = </span>
            <span className="font-bold text-primary">{pb.final_pct.toFixed(2)}%</span>
          </div>
          <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-400">
            ⚠️ Risk controls: max single stock 10–15% of portfolio. Maintain 10–20% cash reserve.
          </div>
        </div>
      )}
    </div>
  )
}
