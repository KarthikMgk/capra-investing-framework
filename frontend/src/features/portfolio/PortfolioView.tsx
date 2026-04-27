import { useNavigate } from "@tanstack/react-router"
import { RefreshCw, TrendingUp, Wallet } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { ErrorMessage } from "@/shared/components/ErrorMessage"
import { useRefresh } from "@/shared/hooks/useRefresh"
import { SignalBadge } from "./SignalBadge"
import { type HoldingWithSignal, usePortfolio } from "./usePortfolio"

// ── Summary cards ────────────────────────────────────────────────────────────

function SummaryCards({ items }: { items: HoldingWithSignal[] }) {
  const totalValue = items.reduce(
    (sum, h) => sum + h.last_price * h.quantity,
    0,
  )

  const signalCounts = items.reduce(
    (acc, h) => {
      const key = h.signal ?? "pending"
      acc[key] = (acc[key] ?? 0) + 1
      return acc
    },
    {} as Record<string, number>,
  )

  const bullish = (signalCounts["strong_buy"] ?? 0) + (signalCounts["buy"] ?? 0)
  const bearish =
    (signalCounts["sell"] ?? 0) + (signalCounts["strong_sell"] ?? 0)

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      <StatCard
        icon={<Wallet className="h-4 w-4 text-muted-foreground" />}
        label="Holdings"
        value={String(items.length)}
      />
      <StatCard
        icon={<TrendingUp className="h-4 w-4 text-muted-foreground" />}
        label="Portfolio Value"
        value={`₹${totalValue.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`}
      />
      <StatCard
        label="Accumulate"
        value={String(bullish)}
        valueClassName="text-emerald-600 dark:text-emerald-400"
      />
      <StatCard
        label="Reduce / Watch"
        value={String(bearish)}
        valueClassName={bearish > 0 ? "text-red-600 dark:text-red-400" : ""}
      />
    </div>
  )
}

function StatCard({
  icon,
  label,
  value,
  valueClassName = "",
}: {
  icon?: React.ReactNode
  label: string
  value: string
  valueClassName?: string
}) {
  return (
    <div className="rounded-lg border bg-card p-4">
      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
        {icon}
        {label}
      </div>
      <p className={`mt-1.5 text-2xl font-semibold tabular-nums tracking-tight ${valueClassName}`}>
        {value}
      </p>
    </div>
  )
}

// ── Holdings table ────────────────────────────────────────────────────────────

function HoldingRow({ holding }: { holding: HoldingWithSignal }) {
  const navigate = useNavigate()

  return (
    <TableRow
      className="cursor-pointer transition-colors hover:bg-muted/50"
      onClick={() => navigate({ to: `/stock/${holding.tradingsymbol}` as never })}
    >
      <TableCell className="font-mono font-semibold tracking-wide text-foreground">
        {holding.tradingsymbol}
      </TableCell>
      <TableCell className="max-w-[180px] truncate text-muted-foreground">
        {holding.name}
      </TableCell>
      <TableCell className="tabular-nums text-right">{holding.quantity}</TableCell>
      <TableCell className="tabular-nums text-right font-medium">
        ₹{holding.last_price.toFixed(2)}
      </TableCell>
      <TableCell className="tabular-nums text-right text-muted-foreground">
        ₹{(holding.last_price * holding.quantity).toLocaleString("en-IN", {
          maximumFractionDigits: 0,
        })}
      </TableCell>
      <TableCell className="text-right">
        <SignalBadge signal={holding.signal} />
      </TableCell>
    </TableRow>
  )
}

function TableSkeleton() {
  return (
    <div className="space-y-2">
      {Array.from({ length: 6 }).map((_, i) => (
        <Skeleton key={i} className="h-12 w-full rounded-md" />
      ))}
    </div>
  )
}

// ── Main view ─────────────────────────────────────────────────────────────────

export function PortfolioView() {
  const { data, isLoading, isError, error, dataUpdatedAt } = usePortfolio()
  const refresh = useRefresh()

  const updatedAt = dataUpdatedAt
    ? new Date(dataUpdatedAt).toLocaleTimeString("en-IN", {
        hour: "2-digit",
        minute: "2-digit",
      })
    : null

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Portfolio</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {updatedAt
              ? `Live prices · updated at ${updatedAt}`
              : "Kite Connect holdings with live quotes"}
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          disabled={refresh.isPending}
          onClick={() => refresh.mutate()}
          className="shrink-0 gap-2"
        >
          <RefreshCw
            className={`h-3.5 w-3.5 ${refresh.isPending ? "animate-spin" : ""}`}
          />
          {refresh.isPending ? "Refreshing…" : "Refresh Data"}
        </Button>
      </div>

      {/* Summary */}
      {!isLoading && !isError && data && (
        <SummaryCards items={data.items} />
      )}

      {/* Table */}
      <div className="rounded-lg border">
        {isLoading ? (
          <div className="p-4">
            <TableSkeleton />
          </div>
        ) : isError ? (
          <div className="p-6">
            <ErrorMessage
              message={
                (error as Error)?.message ??
                "Failed to load portfolio. Is your Kite session active?"
              }
            />
          </div>
        ) : !data?.items.length ? (
          <div className="flex flex-col items-center justify-center gap-2 py-16 text-muted-foreground">
            <Wallet className="h-8 w-8 opacity-30" />
            <p className="text-sm">No holdings found in your Kite account.</p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead className="w-[110px]">Symbol</TableHead>
                <TableHead>Name</TableHead>
                <TableHead className="text-right">Qty</TableHead>
                <TableHead className="text-right">Price</TableHead>
                <TableHead className="text-right">Value</TableHead>
                <TableHead className="text-right">Signal</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.items.map((h) => (
                <HoldingRow key={h.tradingsymbol} holding={h} />
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  )
}
