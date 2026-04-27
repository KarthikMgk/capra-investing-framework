export interface FactorItem {
  name: string
  weight: number
  raw_value: number
  weighted_contribution: number
  signal: "positive" | "negative"
}

export interface PositionBreakdown {
  base_pct: number
  conviction_multiplier: number
  volatility_adjustment: number
  final_pct: number
}

export interface FactorBreakdown {
  factors: FactorItem[]
  roc: number
  asymmetry_index: number
  time_stop_months: number
  position_breakdown: PositionBreakdown
}

export interface StockScoreResponse {
  stock_symbol: string
  composite_score: number
  signal: string
  position_size: number
  computation_timestamp: string
  kite_snapshot_ts: string
  screener_csv_ts: string
  rbi_csv_ts: string
  factor_breakdown: FactorBreakdown
}

export interface StockListItem {
  stock_symbol: string
  name: string
  signal: string | null
}

export interface StockListResponse {
  items: StockListItem[]
  total: number
}
