import { useState } from "react"
import { ChevronDown, ChevronUp } from "lucide-react"
import { Button } from "@/components/ui/button"
import { SignalBadge } from "@/features/portfolio/SignalBadge"
import type { StockScoreResponse } from "@/shared/types/stock"

const SIGNAL_DESCRIPTIONS: Record<string, string> = {
  strong_buy:  "Score above threshold + positive momentum + positive asymmetry — all three dimensions aligned bullish.",
  buy:         "Score positive or improving and at least one of momentum/asymmetry supportive.",
  hold:        "Mixed or flat signals — insufficient conviction to add or reduce.",
  sell:        "Score deteriorating or negative momentum — framework signals caution.",
  strong_sell: "Score below −0.5 — macro and equity conditions clearly negative.",
}

interface Props {
  data: StockScoreResponse
}

export function SignalPillar({ data }: Props) {
  const [open, setOpen] = useState(false)
  const fb = data.factor_breakdown

  return (
    <div className="rounded-lg border bg-card p-5 flex flex-col gap-4">
      <div>
        <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Signal</p>
        <div className="mt-2">
          <SignalBadge signal={data.signal as any} />
        </div>
      </div>

      <Button
        variant="ghost"
        size="sm"
        className="w-fit gap-1.5 text-muted-foreground"
        onClick={() => setOpen((v) => !v)}
      >
        {open ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
        {open ? "Hide" : "Show"} signal detail
      </Button>

      {open && (
        <div className="flex flex-col gap-3 text-sm">
          <p className="text-muted-foreground text-xs">
            {SIGNAL_DESCRIPTIONS[data.signal] ?? "Signal conditions not defined."}
          </p>
          <div className="grid grid-cols-3 gap-3">
            <Metric label="Momentum ROC" value={`${(fb.roc * 100).toFixed(2)}%`} />
            <Metric label="Asymmetry Index" value={fb.asymmetry_index.toFixed(4)} />
            <Metric label="Time Stop" value={`${fb.time_stop_months}m`} />
          </div>
        </div>
      )}
    </div>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-muted/50 p-3">
      <p className="text-[10px] text-muted-foreground uppercase tracking-wider">{label}</p>
      <p className="text-lg font-semibold tabular-nums mt-0.5">{value}</p>
    </div>
  )
}
