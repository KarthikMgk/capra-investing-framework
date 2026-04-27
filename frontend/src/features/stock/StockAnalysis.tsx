import { AxiosError } from "axios"
import { LoadingSpinner } from "@/shared/components/LoadingSpinner"
import { ErrorMessage } from "@/shared/components/ErrorMessage"
import { DataFreshness } from "./DataFreshness"
import { PositionPillar } from "./PositionPillar"
import { ScorePillar } from "./ScorePillar"
import { SignalPillar } from "./SignalPillar"
import { StockSearch } from "./StockSearch"
import { useStockScore } from "./useStockScore"

interface Props {
  symbol?: string
}

export function StockAnalysis({ symbol }: Props) {
  const { data, isLoading, isError, error } = useStockScore(symbol)

  const isNotFound =
    isError &&
    (error as AxiosError<any>)?.response?.data?.detail?.error?.code === "SCORE_NOT_FOUND"

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Stock Analysis</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Decision cockpit — Score · Signal · Position
        </p>
      </div>

      <StockSearch initialSymbol={symbol ?? ""} />

      {symbol && (
        <>
          {isLoading && <LoadingSpinner />}

          {isError && isNotFound && (
            <div className="rounded-lg border border-dashed p-8 text-center text-muted-foreground text-sm">
              No analysis available. Ask admin to run a data refresh.
            </div>
          )}

          {isError && !isNotFound && (
            <ErrorMessage message="Failed to load stock analysis. Please try again." />
          )}

          {data && (
            <>
              <div className="grid gap-4 md:grid-cols-3">
                <ScorePillar data={data} />
                <SignalPillar data={data} />
                <PositionPillar data={data} />
              </div>
              <DataFreshness data={data} />
            </>
          )}
        </>
      )}

      {!symbol && (
        <div className="rounded-lg border border-dashed p-12 text-center text-muted-foreground text-sm">
          Search for a Nifty 50 stock above to view its analysis.
        </div>
      )}
    </div>
  )
}
