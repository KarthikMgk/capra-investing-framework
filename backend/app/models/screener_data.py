import uuid
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ScreenerData(SQLModel, table=True):
    __tablename__ = "screener_data"  # type: ignore[assignment]

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    upload_batch_id: uuid.UUID = Field(index=True)
    uploaded_at: datetime = Field(default_factory=_utcnow)

    symbol: str = Field(max_length=20)
    name: str | None = None
    pe: float | None = None
    pb: float | None = None
    eps: float | None = None
    roe: float | None = None
    debt_to_equity: float | None = None
    revenue_growth: float | None = None
    promoter_holding: float | None = None
