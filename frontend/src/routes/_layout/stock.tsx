import { createFileRoute, Outlet, useChildMatches } from "@tanstack/react-router"
import { Search } from "lucide-react"
import { StockSearch } from "@/features/stock/StockSearch"

export const Route = createFileRoute("/_layout/stock")({
  component: StockLayout,
  head: () => ({ meta: [{ title: "Stock Analysis - Capra Investing" }] }),
})

function StockLayout() {
  const childMatches = useChildMatches()
  const symbolMatch = childMatches.find((m) =>
    m.routeId.includes("$symbol"),
  )
  const currentSymbol = (symbolMatch?.params as any)?.symbol ?? ""

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Stock Analysis</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Decision cockpit — Score · Signal · Position
        </p>
      </div>

      <StockSearch initialSymbol={currentSymbol} />

      <Outlet />

      {!currentSymbol && (
        <div className="rounded-lg border border-dashed p-12 text-center text-muted-foreground text-sm flex flex-col items-center gap-2">
          <Search className="h-6 w-6 opacity-30" />
          Search for a Nifty 50 stock above to view its analysis.
        </div>
      )}
    </div>
  )
}
