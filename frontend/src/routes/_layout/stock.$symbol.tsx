import { createFileRoute } from "@tanstack/react-router"
import { AxiosError } from "axios"
import { LoadingSpinner } from "@/shared/components/LoadingSpinner"
import { ErrorMessage } from "@/shared/components/ErrorMessage"
import { DataFreshness } from "@/features/stock/DataFreshness"
import { PositionPillar } from "@/features/stock/PositionPillar"
import { ScorePillar } from "@/features/stock/ScorePillar"
import { SignalPillar } from "@/features/stock/SignalPillar"
import { useStockScore } from "@/features/stock/useStockScore"

export const Route = createFileRoute("/_layout/stock/$symbol")({
  component: StockDetail,
  head: ({ params }) => ({
    meta: [{ title: `${params.symbol} Analysis - Capra Investing` }],
  }),
})

function StockDetail() {
  const { symbol } = Route.useParams()
  const { data, isLoading, isError, error } = useStockScore(symbol)

  const isNotFound =
    isError &&
    (error as AxiosError<any>)?.response?.data?.detail?.error?.code ===
      "SCORE_NOT_FOUND"

  if (isLoading) return <LoadingSpinner />

  if (isError && isNotFound) {
    return (
      <div className="rounded-lg border border-dashed p-8 text-center text-muted-foreground text-sm">
        No analysis available. Ask admin to run a data refresh.
      </div>
    )
  }

  if (isError) {
    return <ErrorMessage message="Failed to load stock analysis. Please try again." />
  }

  if (!data) return null

  return (
    <div className="flex flex-col gap-4">
      <div className="grid gap-4 md:grid-cols-3">
        <ScorePillar data={data} />
        <SignalPillar data={data} />
        <PositionPillar data={data} />
      </div>
      <DataFreshness data={data} />
    </div>
  )
}
