from pydantic import BaseModel


class FactorItem(BaseModel):
    name: str
    weight: float
    raw_value: float
    weighted_contribution: float
    signal: str  # "positive" | "negative"


class PositionBreakdown(BaseModel):
    base_pct: float
    conviction_multiplier: float
    volatility_adjustment: float
    final_pct: float


class FactorBreakdown(BaseModel):
    factors: list[FactorItem]
    roc: float
    asymmetry_index: float
    time_stop_months: int
    position_breakdown: PositionBreakdown


class StockScoreResponse(BaseModel):
    stock_symbol: str
    composite_score: float
    signal: str
    position_size: float
    computation_timestamp: str   # ISO 8601 UTC
    kite_snapshot_ts: str        # ISO 8601 UTC
    screener_csv_ts: str         # ISO 8601 UTC
    rbi_csv_ts: str              # ISO 8601 UTC
    factor_breakdown: FactorBreakdown
