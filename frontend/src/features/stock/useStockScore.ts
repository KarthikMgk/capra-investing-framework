import { useQuery } from "@tanstack/react-query"
import apiClient from "@/shared/lib/apiClient"
import type { StockScoreResponse } from "@/shared/types/stock"

export function useStockScore(stockSymbol: string | undefined) {
  return useQuery({
    queryKey: ["stock", stockSymbol],
    queryFn: () =>
      apiClient
        .get<StockScoreResponse>(`/api/v1/stocks/${stockSymbol}`)
        .then((r) => r.data),
    enabled: !!stockSymbol,
    staleTime: 0,
  })
}

export function useStockList() {
  return useQuery({
    queryKey: ["stocks"],
    queryFn: () =>
      apiClient.get("/api/v1/stocks").then((r) => r.data),
    staleTime: Infinity,
  })
}
