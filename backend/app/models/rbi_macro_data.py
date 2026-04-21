import uuid
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RBIMacroData(SQLModel, table=True):
    __tablename__ = "rbi_macro_data"  # type: ignore[assignment]

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    upload_batch_id: uuid.UUID
    uploaded_at: datetime = Field(default_factory=_utcnow)

    repo_rate: float | None = None
    credit_growth: float | None = None
    liquidity_indicator: float | None = None
