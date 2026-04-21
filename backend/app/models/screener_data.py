import uuid
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ScreenerData(SQLModel, table=True):
    __tablename__ = "screener_data"  # type: ignore[assignment]

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    upload_batch_id: uuid.UUID
    stock_symbol: str = Field(max_length=20)
    uploaded_at: datetime = Field(default_factory=_utcnow)

    # Screener.in fundamental columns — Optional to handle missing CSV values
    pe_ratio: float | None = None
    pb_ratio: float | None = None
    roe: float | None = None
    roce: float | None = None
    debt_to_equity: float | None = None
    current_ratio: float | None = None
    sales_growth: float | None = None
    profit_growth: float | None = None
    eps: float | None = None
    dividend_yield: float | None = None
