from pydantic import BaseModel


class HoldingData(BaseModel):
    tradingsymbol: str
    quantity: float
    last_price: float


class QuoteData(BaseModel):
    last_price: float
    change: float = 0.0
    change_percent: float = 0.0


class HoldingWithSignal(BaseModel):
    tradingsymbol: str
    name: str
    quantity: float
    last_price: float
    signal: str
    signal_color: str


class PortfolioResponse(BaseModel):
    items: list[HoldingWithSignal]
    total: int
