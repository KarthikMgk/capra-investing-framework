from datetime import datetime

from pydantic import BaseModel


class KiteCredentialsUpdate(BaseModel):
    api_key: str
    access_token: str


class KiteCredentialsStatus(BaseModel):
    api_key_set: bool
    access_token_set: bool
    updated_at: datetime | None
