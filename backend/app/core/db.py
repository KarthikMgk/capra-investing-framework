from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.database import engine  # noqa: F401 — re-exported for existing imports
from app.models import User, UserCreate


def init_db(session: Session) -> None:
    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER_EMAIL)
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER_EMAIL,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            role="admin",
        )
        crud.create_user(session=session, user_create=user_in)
