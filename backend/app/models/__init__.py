from sqlmodel import SQLModel  # noqa: F401 — re-exported for alembic env.py

from app.models.rbi_macro_data import RBIMacroData  # noqa: F401
from app.models.revoked_token import RevokedToken  # noqa: F401
from app.models.score_snapshot import ScoreSnapshot  # noqa: F401
from app.models.screener_data import ScreenerData  # noqa: F401
from app.models.user import (  # noqa: F401
    UpdatePassword,
    User,
    UserBase,
    UserCreate,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)

# Shared API schemas (not table models)
from sqlmodel import SQLModel as _SQLModel


class Message(_SQLModel):
    message: str


class Token(_SQLModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(_SQLModel):
    sub: str | None = None


class NewPassword(_SQLModel):
    token: str
    new_password: str
