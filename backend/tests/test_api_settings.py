from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete, select

from app import crud
from app.core.config import settings
from app.models import User, UserCreate
from app.models.kite_settings import KiteSettings

_API_KEY = "test-api-key-12345"
_ACCESS_TOKEN = "test-access-token-67890"


@pytest.fixture(scope="module")
def viewer_user(db: Session) -> Generator[User, None, None]:
    user = crud.create_user(
        session=db,
        user_create=UserCreate(
            email="viewer_settings_test@example.com",
            password="viewerpassword123",
            role="viewer",
        ),
    )
    yield user
    db.delete(user)
    db.commit()


def _login(client: TestClient, email: str, password: str) -> dict[str, str]:
    r = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": email, "password": password},
    )
    token = r.cookies.get("access_token")
    return {"Cookie": f"access_token={token}"}


def _admin_headers(client: TestClient) -> dict[str, str]:
    return _login(client, settings.FIRST_SUPERUSER_EMAIL, settings.FIRST_SUPERUSER_PASSWORD)


@pytest.fixture(autouse=True)
def cleanup_kite_settings(db: Session) -> Generator[None, None, None]:
    yield
    db.exec(delete(KiteSettings))
    db.commit()


# AC4 + AC10: PUT as admin stores encrypted values (ciphertext != plaintext)
def test_put_kite_settings_admin_encrypts(client: TestClient, db: Session) -> None:
    headers = _admin_headers(client)
    r = client.put(
        f"{settings.API_V1_STR}/settings/kite",
        json={"api_key": _API_KEY, "access_token": _ACCESS_TOKEN},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

    row = db.exec(select(KiteSettings)).first()
    assert row is not None
    assert row.api_key_encrypted != _API_KEY
    assert row.access_token_encrypted != _ACCESS_TOKEN


# AC5: GET as admin returns status flags, no plaintext
def test_get_kite_settings_admin_after_put(client: TestClient, db: Session) -> None:
    headers = _admin_headers(client)
    client.put(
        f"{settings.API_V1_STR}/settings/kite",
        json={"api_key": _API_KEY, "access_token": _ACCESS_TOKEN},
        headers=headers,
    )

    r = client.get(f"{settings.API_V1_STR}/settings/kite", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["api_key_set"] is True
    assert data["access_token_set"] is True
    assert data["updated_at"] is not None
    assert _API_KEY not in str(data)
    assert _ACCESS_TOKEN not in str(data)


# AC6: GET as viewer → 403
def test_get_kite_settings_viewer(
    client: TestClient, db: Session, viewer_user: User
) -> None:
    headers = _login(client, viewer_user.email, "viewerpassword123")
    r = client.get(f"{settings.API_V1_STR}/settings/kite", headers=headers)
    assert r.status_code == 403


# AC6: PUT as viewer → 403
def test_put_kite_settings_viewer(
    client: TestClient, db: Session, viewer_user: User
) -> None:
    headers = _login(client, viewer_user.email, "viewerpassword123")
    r = client.put(
        f"{settings.API_V1_STR}/settings/kite",
        json={"api_key": _API_KEY, "access_token": _ACCESS_TOKEN},
        headers=headers,
    )
    assert r.status_code == 403


# AC7: second PUT is an upsert — no duplicate rows
def test_put_kite_settings_upsert(client: TestClient, db: Session) -> None:
    headers = _admin_headers(client)
    client.put(
        f"{settings.API_V1_STR}/settings/kite",
        json={"api_key": _API_KEY, "access_token": _ACCESS_TOKEN},
        headers=headers,
    )
    client.put(
        f"{settings.API_V1_STR}/settings/kite",
        json={"api_key": "updated-key", "access_token": "updated-token"},
        headers=headers,
    )

    rows = db.exec(select(KiteSettings)).all()
    assert len(rows) == 1


# settings.py:26 — GET before any PUT returns all-false status (no kite_settings row)
def test_get_kite_settings_admin_when_empty(client: TestClient) -> None:
    headers = _admin_headers(client)
    r = client.get(f"{settings.API_V1_STR}/settings/kite", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["api_key_set"] is False
    assert data["access_token_set"] is False
    assert data["updated_at"] is None
