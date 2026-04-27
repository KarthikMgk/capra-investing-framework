import { useQuery } from "@tanstack/react-query"
import apiClient from "@/shared/lib/apiClient"

export interface HoldingWithSignal {
  tradingsymbol: string
  name: string
  quantity: number
  last_price: number
  signal: "strong_buy" | "buy" | "hold" | "sell" | "strong_sell" | null
  signal_color: string | null
}

export interface PortfolioResponse {
  items: HoldingWithSignal[]
  total: number
}

export const PORTFOLIO_QUERY_KEY = ["portfolio"] as const

export function usePortfolio() {
  return useQuery({
    queryKey: PORTFOLIO_QUERY_KEY,
    queryFn: () =>
      apiClient.get<PortfolioResponse>("/api/v1/portfolio").then((r) => r.data),
    staleTime: 0,
  })
}
