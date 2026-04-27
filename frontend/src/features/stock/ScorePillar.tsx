import { useState } from "react"
import { ChevronDown, ChevronUp } from "lucide-react"
import { Button } from "@/components/ui/button"
import { SignalBadge } from "@/features/portfolio/SignalBadge"
import type { StockScoreResponse } from "@/shared/types/stock"

interface Props {
  data: StockScoreResponse
}

export function ScorePillar({ data }: Props) {
  const [open, setOpen] = useState(false)

  return (
    <div className="rounded-lg border bg-card p-5 flex flex-col gap-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Composite Score</p>
          <p className="text-4xl font-bold tabular-nums tracking-tight">
            {data.composite_score >= 0 ? "+" : ""}{data.composite_score.toFixed(4)}
          </p>
        </div>
        <SignalBadge signal={data.signal as any} />
      </div>

      <Button
        variant="ghost"
        size="sm"
        className="w-fit gap-1.5 text-muted-foreground"
        onClick={() => setOpen((v) => !v)}
      >
        {open ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
        {open ? "Hide" : "Show"} factor breakdown
      </Button>

      {open && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-xs text-muted-foreground">
                <th className="pb-2 font-medium">Factor</th>
                <th className="pb-2 font-medium text-right">Weight</th>
                <th className="pb-2 font-medium text-right">Raw</th>
                <th className="pb-2 font-medium text-right">Contribution</th>
                <th className="pb-2 font-medium text-right">Signal</th>
              </tr>
            </thead>
            <tbody>
              {data.factor_breakdown.factors.map((f) => (
                <tr key={f.name} className="border-b last:border-0">
                  <td className="py-2 font-mono text-xs">{f.name}</td>
                  <td className="py-2 text-right tabular-nums text-muted-foreground">
                    {(f.weight * 100).toFixed(0)}%
                  </td>
                  <td className="py-2 text-right tabular-nums">
                    {f.raw_value.toFixed(4)}
                  </td>
                  <td className="py-2 text-right tabular-nums">
                    {f.weighted_contribution.toFixed(4)}
                  </td>
                  <td className="py-2 text-right">
                    <span className={`text-xs font-medium ${f.signal === "positive" ? "text-emerald-600" : "text-red-500"}`}>
                      {f.signal === "positive" ? "▲" : "▼"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
