import uuid
from datetime import datetime

from sqlalchemy import Column, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class ScoreSnapshot(SQLModel, table=True):
    __tablename__ = "score_snapshots"  # type: ignore[assignment]
    __table_args__ = (
        Index("ix_score_snapshots_stock_symbol", "stock_symbol"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    stock_symbol: str = Field(max_length=20)
    composite_score: float
    signal: str = Field(max_length=20)
    position_size: float
    computation_timestamp: datetime
    kite_snapshot_ts: datetime
    screener_csv_ts: datetime
    rbi_csv_ts: datetime
    factor_breakdown: dict = Field(default_factory=dict, sa_column=Column(JSONB))
