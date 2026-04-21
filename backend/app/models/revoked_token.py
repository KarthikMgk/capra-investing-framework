import uuid
from datetime import datetime

from sqlalchemy import Index
from sqlmodel import Field, SQLModel


class RevokedToken(SQLModel, table=True):
    __tablename__ = "revoked_tokens"  # type: ignore[assignment]
    __table_args__ = (
        Index("ix_revoked_tokens_jti", "jti"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    jti: str = Field(unique=True, max_length=255)
    expires_at: datetime
