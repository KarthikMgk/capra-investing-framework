from collections.abc import Generator
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, Request
from sqlmodel import Session, select

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import decode_token
from app.database import engine
from app.models import RevokedToken, User


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]


def get_current_user(request: Request, session: SessionDep) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise AuthenticationError("Not authenticated")

    payload = decode_token(token)

    jti = payload.get("jti")
    if jti:
        revoked = session.exec(
            select(RevokedToken).where(
                RevokedToken.jti == jti,
                RevokedToken.expires_at > datetime.now(timezone.utc),
            )
        ).first()
        if revoked:
            raise AuthenticationError("Token has been revoked")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token payload")

    user = session.get(User, user_id)
    if not user:
        raise AuthenticationError("User not found")
    if not user.is_active:
        raise AuthenticationError("User account is inactive")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_kite_client(session: SessionDep) -> "KiteClient":
    """Dependency that constructs a KiteClient — override in tests with mock."""
    from app.services.kite_client import KiteClient
    return KiteClient(session)


def require_admin(current_user: CurrentUser) -> User:
    if current_user.role != "admin":
        raise AuthorizationError("Admin access required")
    return current_user
