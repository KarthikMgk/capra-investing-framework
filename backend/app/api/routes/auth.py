import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Request, Response
from sqlmodel import delete

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.core.config import settings
from app.core.exceptions import AuthenticationError
from app.core.security import create_access_token, decode_token
from app.models import RevokedToken
from app.schemas.auth import LoginRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

_TOKEN_EXPIRE_HOURS = 24


@router.post("/login", response_model=UserResponse)
def login(body: LoginRequest, response: Response, session: SessionDep) -> Any:
    user = crud.authenticate(session=session, email=body.email, password=body.password)
    if not user:
        raise AuthenticationError("Invalid email or password.", code="INVALID_CREDENTIALS")

    session.exec(
        delete(RevokedToken).where(RevokedToken.expires_at < datetime.now(timezone.utc))
    )
    session.commit()

    jti = str(uuid.uuid4())
    token = create_access_token(
        subject=str(user.id),
        jti=jti,
        role=user.role,
        expires_delta=timedelta(hours=_TOKEN_EXPIRE_HOURS),
    )

    secure = settings.ENVIRONMENT == "production"
    samesite: str = "strict" if settings.ENVIRONMENT == "production" else "lax"

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=_TOKEN_EXPIRE_HOURS * 3600,
    )

    return UserResponse(id=user.id, email=user.email, role=user.role)


@router.post("/logout")
def logout(request: Request, response: Response, session: SessionDep) -> dict[str, str]:
    token = request.cookies.get("access_token")
    if token:
        try:
            payload = decode_token(token)
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti and exp:
                expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
                session.add(RevokedToken(jti=jti, expires_at=expires_at))
                session.commit()
        except AuthenticationError:
            pass

    response.delete_cookie("access_token")
    return {"status": "ok"}


@router.get("/me", response_model=UserResponse)
def me(current_user: CurrentUser) -> Any:
    return UserResponse(id=current_user.id, email=current_user.email, role=current_user.role)
