import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Text
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class KiteSettings(SQLModel, table=True):
    __tablename__ = "kite_settings"  # type: ignore[assignment]

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    api_key_encrypted: str = Field(sa_type=Text)
    access_token_encrypted: str = Field(sa_type=Text)
    updated_at: datetime = Field(
        default_factory=_utcnow,
        sa_type=DateTime(timezone=True),  # type: ignore[call-overload]
    )
