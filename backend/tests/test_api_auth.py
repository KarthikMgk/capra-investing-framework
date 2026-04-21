import uuid
from datetime import timedelta
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.core.security import create_access_token, decode_token
from app.models import RevokedToken, User, UserCreate


@pytest.fixture(scope="module")
def viewer_user(db: Session) -> Generator[User, None, None]:
    user = crud.create_user(
        session=db,
        user_create=UserCreate(email="viewer_auth_test@example.com", password="viewerpassword123", role="viewer"),
    )
    yield user
    db.delete(user)
    db.commit()


def _login_superuser(client: TestClient) -> str:
    r = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": settings.FIRST_SUPERUSER_EMAIL, "password": settings.FIRST_SUPERUSER_PASSWORD},
    )
    assert r.status_code == 200
    token = r.cookies.get("access_token")
    assert token
    return token


# AC1: login with correct credentials → 200, UserResponse body, cookie set, no token in body
def test_login_returns_user_response_and_cookie(client: TestClient) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": settings.FIRST_SUPERUSER_EMAIL, "password": settings.FIRST_SUPERUSER_PASSWORD},
    )
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    assert "email" in data
    assert "role" in data
    assert "access_token" not in data
    assert "hashed_password" not in data
    assert "access_token" in r.cookies


# AC2: wrong password → 401, INVALID_CREDENTIALS
def test_login_wrong_password(client: TestClient) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": settings.FIRST_SUPERUSER_EMAIL, "password": "wrongpassword"},
    )
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "INVALID_CREDENTIALS"


# AC2: non-existent email → 401, INVALID_CREDENTIALS
def test_login_nonexistent_email(client: TestClient) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": "ghost@example.com", "password": "somepassword"},
    )
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "INVALID_CREDENTIALS"


# AC3: logout inserts JTI, clears cookie → 200 {"status": "ok"}
def test_logout_blacklists_jti_and_clears_cookie(client: TestClient, db: Session) -> None:
    token = _login_superuser(client)

    r = client.post(
        f"{settings.API_V1_STR}/auth/logout",
        headers={"Cookie": f"access_token={token}"},
    )
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

    payload = decode_token(token)
    jti = payload["jti"]
    revoked = db.exec(select(RevokedToken).where(RevokedToken.jti == jti)).first()
    assert revoked is not None


# AC4: revoked token → 401
def test_revoked_token_blocked(client: TestClient) -> None:
    token = _login_superuser(client)

    client.post(
        f"{settings.API_V1_STR}/auth/logout",
        headers={"Cookie": f"access_token={token}"},
    )

    r = client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Cookie": f"access_token={token}"},
    )
    assert r.status_code == 401


# AC5: GET /auth/me with valid cookie → 200, correct user fields
def test_me_with_valid_cookie(client: TestClient) -> None:
    token = _login_superuser(client)
    r = client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Cookie": f"access_token={token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == settings.FIRST_SUPERUSER_EMAIL
    assert data["role"] == "admin"
    assert "id" in data


# AC6: expired token → 401
def test_expired_token_blocked(client: TestClient) -> None:
    expired_token = create_access_token(
        subject=str(uuid.uuid4()),
        jti=str(uuid.uuid4()),
        role="viewer",
        expires_delta=timedelta(seconds=-1),
    )
    r = client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Cookie": f"access_token={expired_token}"},
    )
    assert r.status_code == 401


# AC7: viewer calling admin route → 403, INSUFFICIENT_PERMISSIONS
def test_viewer_cannot_access_admin_route(client: TestClient, viewer_user: User) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": "viewer_auth_test@example.com", "password": "viewerpassword123"},
    )
    assert r.status_code == 200, f"Viewer login failed: {r.json()}"
    token = r.cookies.get("access_token")

    r2 = client.get(
        f"{settings.API_V1_STR}/users/",
        headers={"Cookie": f"access_token={token}"},
    )
    assert r2.status_code == 403
    assert r2.json()["error"]["code"] == "INSUFFICIENT_PERMISSIONS"


# AC8: no cookie → 401
def test_protected_endpoint_without_cookie() -> None:
    from app.main import app

    with TestClient(app) as fresh_client:
        r = fresh_client.get(f"{settings.API_V1_STR}/auth/me")
        assert r.status_code == 401


# AC11: expired revoked_tokens rows deleted on next login
def test_login_cleans_expired_revoked_tokens(client: TestClient, db: Session) -> None:
    expired_jti = str(uuid.uuid4())
    from datetime import datetime, timezone

    expired_row = RevokedToken(
        jti=expired_jti,
        expires_at=datetime(2000, 1, 1, tzinfo=timezone.utc),
    )
    db.add(expired_row)
    db.commit()

    count_before = db.exec(
        select(RevokedToken).where(RevokedToken.jti == expired_jti)
    ).first()
    assert count_before is not None

    _login_superuser(client)

    count_after = db.exec(
        select(RevokedToken).where(RevokedToken.jti == expired_jti)
    ).first()
    assert count_after is None
